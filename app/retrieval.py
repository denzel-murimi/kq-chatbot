"""
Vector similarity search over the policy knowledge base (Issue #6).

Given a passenger's question, embed it as a RETRIEVAL_QUERY and return the most
similar policy chunks by cosine distance. Results carry a similarity score in
0..1 (1 = identical direction), which the RAG pipeline in Issue #7 uses to decide
whether the best match is good enough to answer from, or whether to fall back.

The cosine-distance operator (<=>) and the vector type live in the "extensions"
schema (where 001_init.sql installed pgvector), so both are schema-qualified in
the query. This avoids depending on the database search_path, which is not
reliable through a transaction-mode connection pooler.
"""
from __future__ import annotations

import asyncio

from app.embeddings import embed_query

# OPERATOR(extensions.<=>) references the cosine-distance operator by schema, so
# it resolves regardless of search_path. 1 - distance = cosine similarity.
_RETRIEVE_SQL = """
select
    id,
    doc_title,
    content,
    1 - (embedding OPERATOR(extensions.<=>) $1::extensions.vector) as similarity
from public.policy_chunks
order by embedding OPERATOR(extensions.<=>) $1::extensions.vector
limit $2
"""


def _vec_literal(vec: list[float]) -> str:
    return "[" + ",".join(repr(x) for x in vec) + "]"


async def retrieve(db, query: str, k: int = 4) -> list[dict]:
    """Return the top-k most similar chunks. `db` is an asyncpg pool or
    connection. The embedding call is synchronous, so it is run off the event
    loop to keep the async caller unblocked."""
    query_vec = await asyncio.to_thread(embed_query, query)
    rows = await db.fetch(_RETRIEVE_SQL, _vec_literal(query_vec), k)
    return [
        {
            "id": r["id"],
            "doc_title": r["doc_title"],
            "content": r["content"],
            "similarity": float(r["similarity"]),
        }
        for r in rows
    ]
