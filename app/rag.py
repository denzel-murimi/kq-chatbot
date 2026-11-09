"""
Retrieval-augmented generation with a hallucination gate (Issue #7).

Flow for an informational question:
  1. Retrieve the most similar policy chunks (Issue #6). Retrieval and embeddings
     use Google Gemini (app/embeddings.py) and are unchanged.
  2. GATE: if the best chunk's similarity is below the threshold, return the
     hardcoded fallback WITHOUT calling the language model at all. This makes the
     "zero hallucination" property architectural: the model is never asked to
     answer a question the knowledge base cannot support.
  3. Otherwise pass the retrieved chunks to the generation model with a strict
     answer-only-from-context instruction, and return the grounded answer with
     its sources.

Answer generation runs on Groq rather than Gemini. Gemini's free tier
caps generation at ~20 requests/day, which cannot support iterative testing or
the planned user-acceptance testing; Groq's free tier is far larger and needs no
billing. Embeddings remain on Gemini, so the vector schema and retrieval are
unaffected. Only this generation step changed.

The generation call retries transient server errors with exponential backoff and
returns a clear "service busy" message (status "unavailable") if the model stays
down — distinct from the hallucination fallback, so an outage is never mistaken
for "no information".

The threshold default (0.6) was chosen from observed retrieval scores: real
policy questions scored ~0.69-0.76 while an out-of-scope question scored ~0.51.
Threshold and model are configurable via environment variables.
"""
from __future__ import annotations

import asyncio
import os
import time
from functools import lru_cache

import groq
from groq import Groq

from app.retrieval import retrieve

# Same default as app/entities.py. The old default (llama-3.1-8b-instant) is no
# longer served by Groq, so any process that imported this module before loading
# .env silently got "service busy" for every grounded answer.
GENERATION_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.6"))

_MAX_ATTEMPTS = 3

FALLBACK_RESPONSE = (
    "I don't have verified Kenya Airways information to answer that confidently. "
    "Please contact Kenya Airways customer service so an agent can help you accurately."
)
SERVICE_UNAVAILABLE_RESPONSE = (
    "I found the relevant Kenya Airways policy, but the assistant service is busy "
    "right now. Please try again in a moment."
)
# The model must signal "cannot answer" with an exact token rather than a polite
# refusal in its own words. A worded refusal is indistinguishable from an answer,
# so it used to be returned as grounded, with sources shown under "I don't know".
NO_ANSWER_TOKEN = "NO_ANSWER"
SYSTEM_INSTRUCTION = (
    "You are a Kenya Airways passenger assistant. Answer the passenger's question "
    "using ONLY the policy context provided. Never invent policy details, figures, "
    "or rules, and never apply a rule stated for one case (for example domestic "
    "flights) to a different case (for example international flights). If the "
    f"context does not contain the answer, reply with exactly {NO_ANSWER_TOKEN} and "
    "nothing else. Keep the answer concise, factual, and friendly. Respond in short "
    "plain sentences and simple bullet points only; do not use markdown tables."
)


@lru_cache(maxsize=1)
def _client() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def _generate(query: str, context: str) -> str:
    """Call Groq, retrying transient server/connection errors with exponential
    backoff. A rate-limit (429) or other client error is not retried; it is
    raised so the caller can surface it. Raises on final failure."""
    last_error: Exception | None = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            resp = _client().chat.completions.create(
                model=GENERATION_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user",
                     "content": f"Policy context:\n{context}\n\nPassenger question: {query}"},
                ],
                temperature=0.1,
                # The available Groq models are reasoning models: without these
                # they spend the whole budget "thinking" and return empty content.
                # Keep reasoning minimal (this is extract-from-context, not a
                # puzzle), route it to its own field so `content` is the clean
                # answer, and leave room for both.
                reasoning_effort="low",
                reasoning_format="parsed",
                max_completion_tokens=512,
            )
            return (resp.choices[0].message.content or "").strip()
        except (groq.InternalServerError, groq.APIConnectionError) as e:
            last_error = e
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(1.5 * (2 ** attempt))  # 1.5s, then 3s
                continue
            raise
    assert last_error is not None
    raise last_error


async def answer_informational(db, query: str, k: int = 4) -> dict:
    """Retrieve, apply the gate, and (only if grounded) generate an answer.

    Returns:
      reply          - text to show the passenger
      status         - 'grounded' | 'fallback' | 'unavailable'
      grounded       - True only when a grounded answer was produced
      top_similarity - best retrieval score (for logging/debugging)
      sources        - source documents (grounded answers only)
      timings        - stage latencies in ms: 'retrieve', plus 'generate' when
                       the model was called
    """
    t0 = time.perf_counter()
    chunks = await retrieve(db, query, k=k)
    t_retrieve = int((time.perf_counter() - t0) * 1000)
    top = chunks[0]["similarity"] if chunks else 0.0

    # The gate: below threshold -> fallback, no model call.
    if not chunks or top < SIMILARITY_THRESHOLD:
        return {"reply": FALLBACK_RESPONSE, "status": "fallback",
                "grounded": False, "top_similarity": top, "sources": [],
                "timings": {"retrieve": t_retrieve}}

    context = "\n\n".join(f"[{c['doc_title']}]\n{c['content']}" for c in chunks)
    t1 = time.perf_counter()
    try:
        reply = await asyncio.to_thread(_generate, query, context)
    except groq.GroqError:
        # Grounding succeeded but generation failed (busy / rate limited). This
        # is NOT a hallucination fallback — the policy was found.
        t_generate = int((time.perf_counter() - t1) * 1000)
        return {"reply": SERVICE_UNAVAILABLE_RESPONSE, "status": "unavailable",
                "grounded": False, "top_similarity": top, "sources": [],
                "timings": {"retrieve": t_retrieve, "generate": t_generate}}
    t_generate = int((time.perf_counter() - t1) * 1000)

    # Empty output or the refusal token -> the same fallback as the gate, with no
    # sources, so "I don't know" can never be presented as a sourced answer.
    if not reply or reply.strip().strip("*_`\"'. ").upper().startswith(NO_ANSWER_TOKEN):
        return {"reply": FALLBACK_RESPONSE, "status": "fallback",
                "grounded": False, "top_similarity": top, "sources": [],
                "timings": {"retrieve": t_retrieve, "generate": t_generate}}

    sources = [{"doc_title": c["doc_title"], "similarity": round(c["similarity"], 3)} for c in chunks]
    return {"reply": reply, "status": "grounded",
            "grounded": True, "top_similarity": top, "sources": sources,
            "timings": {"retrieve": t_retrieve, "generate": t_generate}}