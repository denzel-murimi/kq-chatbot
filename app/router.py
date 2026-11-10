"""
Semantic router (Issue #4) — Google Gemini embeddings.

Classifies an incoming passenger message as 'informational' (answerable from
policy documents, handled by the RAG pipeline), 'transactional' (an action on a
booking, handled by the slot-filling engine) or 'out_of_scope' (unrelated to
Kenya Airways travel, answered with a fixed message saying what the assistant
can help with).

How it works, in one sentence: embed the message, measure cosine similarity to
a small set of labelled example phrases, and pick the closer class. No trained
model — the example phrases ARE the configuration, and every decision comes with
a similarity score we can log and explain.

Embeddings come from Gemini's gemini-embedding-001 with output_dimensionality
set to 1536, which keeps the database schema (VECTOR(1536)) unchanged.
"""
from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
from google import genai
from google.genai import types

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 1536  # matches db/migrations/001_init.sql; Gemini supports this via Matryoshka

# Labelled example phrases. Add more as real test queries surface things these
# don't cover well — this list is meant to grow, not stay fixed.
EXAMPLES: dict[str, list[str]] = {
    "informational": [
        "What is the baggage allowance for economy class?",
        "How much hand luggage can I bring on board?",
        "When does online check-in open and close?",
        "Do I need a transit visa to connect through Nairobi?",
        "Can I travel with my pet in the cabin?",
        "What items are not allowed in checked baggage?",
        "How early should I get to the airport for an international flight?",
        "What is your policy on flight delays and compensation?",
        "What is your policy on changing a flight?",
        "Can I change my flight to another date?",
        "What are the rules for cancelling a booking?",
        "Is there a fee to change my ticket?",
        "What is your refund policy?",
        # "my flight" / "my trip" wording on document questions pulled them toward
        # the flight-status exemplars ("What documents do I need to carry for my
        # flight?" asked for a PNR). These teach the boundary: status/on-time is
        # transactional; documents/visa/entry requirements are informational.
        "What documents do I need to carry for my flight?",
        "What travel documents are required for my trip?",
        "Do I need a visa for my destination?",
        "What do I need to bring to the airport?",
        "What are the entry requirements for Kenya?",
    ],
    "transactional": [
        "I want to change my seat on my booking.",
        "Check me in for my flight.",
        "What is the status of my flight?",
        "Can you look up my booking with reference ABC123?",
        "I need to update the last name on my reservation.",
        "Cancel my booking please.",
        "Move me to a window seat.",
        "Is my flight KQ100 on time today?",
    ],
    # Off-domain requests. Without this class every message had to be either
    # informational or transactional, so "What is the weather like in Paris?"
    # was sent down the booking path (0.72 transactional vs 0.70 informational).
    # Keep these clearly unrelated to travel so they never compete with real
    # policy or booking questions.
    "out_of_scope": [
        "What's the weather forecast for this weekend?",
        "What is the capital of France?",
        "Tell me a joke.",
        "Who won the match last night?",
        "Can you help with my homework?",
        "What time is it right now?",
    ],
}


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    # Built lazily (first call) so importing this module never requires the key.
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def _normalise(vec: list[float]) -> list[float]:
    """L2-normalise. Gemini returns a unit vector at its native 3072 dims, but a
    Matryoshka-truncated vector (1536 here) must be re-normalised before it is
    used for cosine similarity or stored for cosine distance."""
    arr = np.asarray(vec, dtype=float)
    norm = np.linalg.norm(arr)
    return (arr / norm).tolist() if norm else arr.tolist()


def _embed(text: str, task_type: str = "SEMANTIC_SIMILARITY") -> list[float]:
    resp = _client().models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIM,
            task_type=task_type,
        ),
    )
    return _normalise(resp.embeddings[0].values)


def _embed_many(texts: list[str], task_type: str = "SEMANTIC_SIMILARITY") -> list[list[float]]:
    resp = _client().models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIM,
            task_type=task_type,
        ),
    )
    return [_normalise(e.values) for e in resp.embeddings]


@lru_cache(maxsize=1)
def _example_vectors() -> dict[str, list[list[float]]]:
    """Embed every example phrase once, on first use, and cache for the process."""
    out: dict[str, list[list[float]]] = {}
    for label, phrases in EXAMPLES.items():
        out[label] = _embed_many(phrases)
    return out


def _cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom else 0.0


# Fail toward the safer pipeline. Every misroute seen in testing was an
# informational question sent to transactional, never the reverse, and a wrong
# "please give me your PNR" is far more jarring than a policy answer (which the
# RAG hallucination gate already guards). So when transactional only narrowly
# beats informational, the message goes to informational instead.
# Calibration (gemini-embedding-001): genuine transactional requests won by
# +0.046 to +0.158; the closest was "What time does my flight leave?" (+0.046).
# 0.03 stays below that so real requests are unaffected.
TRANSACTIONAL_MIN_MARGIN = 0.03


def classify(message: str, prefer_informational: bool = True) -> dict:
    """
    Returns a dict:
      route    -> 'informational' | 'transactional' | 'out_of_scope'
      score    -> best cosine similarity (0..1)
      margin   -> gap to the runner-up class (how confident the pick is)
      scores   -> per-class best similarity, for logging/debugging
      biased   -> True if a near-tie was resolved to informational

    prefer_informational applies the TRANSACTIONAL_MIN_MARGIN safeguard. Pass
    False while a booking request is collecting details, where short replies
    (a PNR, a surname) belong to slot-filling.
    """
    query_vec = _embed(message)
    vectors = _example_vectors()
    scores = {label: max(_cosine(query_vec, v) for v in vecs) for label, vecs in vectors.items()}
    route = max(scores, key=scores.get)
    ordered = sorted(scores.values(), reverse=True)
    margin = ordered[0] - ordered[1] if len(ordered) > 1 else ordered[0]

    biased = False
    if (
        prefer_informational
        and route == "transactional"
        and scores["transactional"] - scores["informational"] < TRANSACTIONAL_MIN_MARGIN
    ):
        route = "informational"
        margin = scores["informational"] - scores["transactional"]  # negative: overridden pick
        biased = True

    return {"route": route, "score": scores[route], "margin": margin, "scores": scores, "biased": biased}