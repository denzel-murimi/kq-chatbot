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

Answer generation runs on Groq (Llama) rather than Gemini. Gemini's free tier
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

GENERATION_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
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
SYSTEM_INSTRUCTION = (
    "You are a Kenya Airways passenger assistant. Answer the passenger's question "
    "using ONLY the policy context provided. If the context does not contain the "
    "answer, say you do not have that information and suggest contacting Kenya "
    "Airways support. Never invent policy details, figures, or rules. Keep the "
    "answer concise, factual, and friendly. Respond in short plain sentences "
    "and simple bullet points only; do not use markdown tables."
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
                max_completion_tokens=1024,
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
    """
    chunks = await retrieve(db, query, k=k)
    top = chunks[0]["similarity"] if chunks else 0.0

    # The gate: below threshold -> fallback, no model call.
    if not chunks or top < SIMILARITY_THRESHOLD:
        return {"reply": FALLBACK_RESPONSE, "status": "fallback",
                "grounded": False, "top_similarity": top, "sources": []}

    context = "\n\n".join(f"[{c['doc_title']}]\n{c['content']}" for c in chunks)
    try:
        reply = await asyncio.to_thread(_generate, query, context)
    except groq.GroqError:
        # Grounding succeeded but generation failed (busy / rate limited). This
        # is NOT a hallucination fallback — the policy was found.
        return {"reply": SERVICE_UNAVAILABLE_RESPONSE, "status": "unavailable",
                "grounded": False, "top_similarity": top, "sources": []}

    if not reply:
        return {"reply": FALLBACK_RESPONSE, "status": "fallback",
                "grounded": False, "top_similarity": top, "sources": []}

    sources = [{"doc_title": c["doc_title"], "similarity": round(c["similarity"], 3)} for c in chunks]
    return {"reply": reply, "status": "grounded",
            "grounded": True, "top_similarity": top, "sources": sources}