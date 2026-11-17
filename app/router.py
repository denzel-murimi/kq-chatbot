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
        "is there ground transportation in oakland",
    ],
    # Flight search, fares and new bookings: also out of scope, but these
    # passengers get a reply pointing them to kenya-airways.com and the KQ app.
    # classify() folds this class into 'out_of_scope' (see OUT_OF_SCOPE_TOPICS),
    # so routes, margins and logs are unchanged; it only sets result["topic"].
    "flight_search": [
        "show me flights from boston to denver on tuesday morning",
        "what flights are there from atlanta to baltimore",
        "is there a flight on american airlines from boston to denver",
        "what are the cheapest flights from pittsburgh to atlanta",
        "all one way flights between boston and philadelphia",
        "I need a flight from Nairobi to London next week",
        "show me fares from miami to new york",
        "what's the lowest round trip fare from dallas to atlanta",
        "which airlines fly from boston to san francisco",
        # Kenyan and regional routes, which is what passengers actually ask
        # about; the ATIS phrases above are all US routes.
        "Are there flights from Nairobi to Kisumu on Saturday?",
        "Do you fly from Mombasa to Dar es Salaam?",
        "When is the next flight to Entebbe?",
    ],
}

# Example classes that are routed as 'out_of_scope', mapped to the topic they
# report. "out_of_scope" itself is the general, unrelated-to-travel topic.
OUT_OF_SCOPE_TOPICS = {"out_of_scope": "general", "flight_search": "flight_search"}


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
# beats the best other class, the message goes to that class instead
# (informational or out_of_scope, whichever scored higher).
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
      biased   -> True if a near-tie win for transactional was handed to the
                  runner-up (informational or out_of_scope)
      topic    -> for out_of_scope: 'general' | 'flight_search'; otherwise None

    prefer_informational applies the TRANSACTIONAL_MIN_MARGIN safeguard. Pass
    False while a booking request is collecting details, where short replies
    (a PNR, a surname) belong to slot-filling.
    """
    query_vec = _embed(message)
    vectors = _example_vectors()
    by_class = {label: max(_cosine(query_vec, v) for v in vecs) for label, vecs in vectors.items()}
    # Fold the out-of-scope sub-classes into one 'out_of_scope' score, so the
    # route and margin are computed over the three routes only.
    oos_class = max(OUT_OF_SCOPE_TOPICS, key=by_class.get)
    scores = {label: s for label, s in by_class.items() if label not in OUT_OF_SCOPE_TOPICS}
    scores["out_of_scope"] = by_class[oos_class]
    route = max(scores, key=scores.get)
    ordered = sorted(scores.values(), reverse=True)
    margin = ordered[0] - ordered[1] if len(ordered) > 1 else ordered[0]

    biased = False
    if prefer_informational and route == "transactional":
        # Compare against the best non-transactional class, not just
        # informational: a flight-search query can tie transactional with
        # out_of_scope, and must not be pushed to informational.
        runner_up = max(("informational", "out_of_scope"), key=scores.get)
        if scores["transactional"] - scores[runner_up] < TRANSACTIONAL_MIN_MARGIN:
            route = runner_up
            margin = scores[runner_up] - scores["transactional"]  # negative: overridden pick
            biased = True

    topic = OUT_OF_SCOPE_TOPICS[oos_class] if route == "out_of_scope" else None

    return {
        "route": route,
        "score": scores[route],
        "margin": margin,
        "scores": scores,
        "biased": biased,
        "topic": topic,
    }