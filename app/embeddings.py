"""
Shared Gemini embedding helper.

Centralises the embedding contract for the whole project: model name, the 1536
output dimensionality that matches the database schema, L2 normalisation of the
Matryoshka-truncated vectors, and the task type. Retrieval uses two different
task types on purpose: documents are embedded as RETRIEVAL_DOCUMENT and a user's
question as RETRIEVAL_QUERY, which is how Gemini is designed to be used for
search and improves match quality over treating both the same way.
"""
from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
from google import genai
from google.genai import types

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 1536  # matches extensions.vector(1536) in db/migrations/003


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def _normalise(vec: list[float]) -> list[float]:
    arr = np.asarray(vec, dtype=float)
    norm = np.linalg.norm(arr)
    return (arr / norm).tolist() if norm else arr.tolist()


def embed_texts(texts: list[str], task_type: str) -> list[list[float]]:
    """Embed a batch of texts. task_type is 'RETRIEVAL_DOCUMENT' for stored
    chunks or 'RETRIEVAL_QUERY' for a user question."""
    resp = _client().models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIM,
            task_type=task_type,
        ),
    )
    return [_normalise(e.values) for e in resp.embeddings]


def embed_query(text: str) -> list[float]:
    return embed_texts([text], task_type="RETRIEVAL_QUERY")[0]
