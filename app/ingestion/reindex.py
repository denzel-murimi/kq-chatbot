"""
Reindex the policy corpus into the policy_chunks table.

Reads every .md file under the corpus directory (SOURCES.md is skipped), splits
each into chunks, embeds them with Gemini as RETRIEVAL_DOCUMENT vectors, and
loads them into policy_chunks. The load is idempotent per document: a document's
existing chunks are deleted before its new chunks are inserted, so re-running
after editing a file refreshes only that file and never creates duplicates.

Usage (repo root, venv active, .env with GEMINI_API_KEY and DATABASE_URL):
    python -m app.ingestion.reindex
"""
from __future__ import annotations

import asyncio
import glob
import os

import asyncpg
from dotenv import load_dotenv

from app.embeddings import embed_texts
from app.ingestion.chunk import chunk_text

load_dotenv()

CORPUS_DIR = os.getenv("CORPUS_DIR", "corpus")
EMBED_BATCH = 20  # embed in modest batches


def _doc_title(text: str, filename: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return os.path.splitext(os.path.basename(filename))[0]


def _vec_literal(vec: list[float]) -> str:
    return "[" + ",".join(repr(x) for x in vec) + "]"


async def reindex() -> None:
    files = sorted(
        f for f in glob.glob(os.path.join(CORPUS_DIR, "**", "*.md"), recursive=True)
        if os.path.basename(f).lower() != "sources.md"
    )
    if not files:
        print(f"No .md files found under {CORPUS_DIR!r}.")
        return

    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], statement_cache_size=0)
    total_chunks = 0
    try:
        for path in files:
            text = open(path, encoding="utf-8").read()
            title = _doc_title(text, path)
            chunks = chunk_text(text)
            if not chunks:
                continue

            # embed in batches
            vectors: list[list[float]] = []
            for i in range(0, len(chunks), EMBED_BATCH):
                batch = chunks[i:i + EMBED_BATCH]
                vectors.extend(embed_texts(batch, task_type="RETRIEVAL_DOCUMENT"))

            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("delete from public.policy_chunks where doc_title = $1", title)
                    await conn.executemany(
                        "insert into public.policy_chunks (doc_title, content, embedding) "
                        "values ($1, $2, $3::extensions.vector)",
                        [(title, chunk, _vec_literal(vec)) for chunk, vec in zip(chunks, vectors)],
                    )
            total_chunks += len(chunks)
            print(f"  {title}: {len(chunks)} chunks")

        row = await pool.fetchrow("select count(*) as n from public.policy_chunks")
        print(f"\nReindex complete. {total_chunks} chunks written this run; "
              f"{row['n']} rows now in policy_chunks.")
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(reindex())