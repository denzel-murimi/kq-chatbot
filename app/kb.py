"""
Knowledge base operations (admin sprint).

policy_documents holds the editable SOURCE text of each policy; policy_chunks
holds the embedded INDEX generated from it. These functions keep the two
consistent: writing or deleting a document also updates its chunks in
policy_chunks, and re-indexing regenerates every document's chunks. The chunker
and the embedding call are the same ones the initial ingestion used
(app.ingestion.chunk, app.embeddings), so the admin path and the batch path
produce identical vectors.

All of this runs as the postgres role the backend already uses; the two-wall RLS
on both tables is unchanged.
"""
from __future__ import annotations

import asyncio

from app.embeddings import embed_texts
from app.ingestion.chunk import chunk_text

EMBED_BATCH = 20  # embed in modest batches, matching reindex.py


def _vec_literal(vec: list[float]) -> str:
    return "[" + ",".join(repr(x) for x in vec) + "]"


async def _embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Embed chunks as RETRIEVAL_DOCUMENT vectors. embed_texts is synchronous
    (the Gemini client), so it is run off the event loop."""
    vectors: list[list[float]] = []
    for i in range(0, len(chunks), EMBED_BATCH):
        batch = chunks[i:i + EMBED_BATCH]
        vectors.extend(await asyncio.to_thread(embed_texts, batch, task_type="RETRIEVAL_DOCUMENT"))
    return vectors


async def _replace_chunks(conn, title: str, content: str) -> int:
    """Re-chunk and re-embed one document's content into policy_chunks, replacing
    any existing chunks for that title. Returns the number of chunks written."""
    chunks = chunk_text(content)
    await conn.execute("delete from public.policy_chunks where doc_title = $1", title)
    if not chunks:
        return 0
    vectors = await _embed_chunks(chunks)
    await conn.executemany(
        "insert into public.policy_chunks (doc_title, content, embedding) "
        "values ($1, $2, $3::extensions.vector)",
        [(title, c, _vec_literal(v)) for c, v in zip(chunks, vectors)],
    )
    return len(chunks)


async def list_documents(db) -> list[dict]:
    """Every source document with its chunk count in the index."""
    rows = await db.fetch(
        "select d.title, d.updated_at, "
        "  (select count(*) from public.policy_chunks c where c.doc_title = d.title) as chunks "
        "from public.policy_documents d order by d.title"
    )
    return [{"title": r["title"], "updated_at": r["updated_at"].isoformat(),
             "chunks": r["chunks"]} for r in rows]


async def get_document(db, title: str) -> dict | None:
    r = await db.fetchrow(
        "select title, content, updated_at from public.policy_documents where title = $1", title)
    if r is None:
        return None
    return {"title": r["title"], "content": r["content"], "updated_at": r["updated_at"].isoformat()}


async def upsert_document(db, title: str, content: str) -> int:
    """Create or update a document and regenerate its chunks in one transaction.
    Returns the chunk count."""
    async with db.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "insert into public.policy_documents (title, content, updated_at) "
                "values ($1, $2, now()) "
                "on conflict (title) do update set content = excluded.content, updated_at = now()",
                title, content)
            return await _replace_chunks(conn, title, content)


async def delete_document(db, title: str) -> bool:
    """Remove a document and its chunks. Returns True if a document was removed."""
    async with db.acquire() as conn:
        async with conn.transaction():
            await conn.execute("delete from public.policy_chunks where doc_title = $1", title)
            res = await conn.execute("delete from public.policy_documents where title = $1", title)
    return res.endswith(" 1")  # asyncpg returns e.g. "DELETE 1"


async def reindex_all(db) -> dict:
    """Regenerate policy_chunks from every document. Returns counts."""
    docs = await db.fetch("select title, content from public.policy_documents order by title")
    total = 0
    async with db.acquire() as conn:
        for d in docs:
            async with conn.transaction():
                total += await _replace_chunks(conn, d["title"], d["content"])
    return {"documents": len(docs), "chunks": total}