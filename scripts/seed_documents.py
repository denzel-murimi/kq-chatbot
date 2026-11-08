"""
One-time seed: load the corpus/*.md files into policy_documents, and regenerate
their chunks in policy_chunks, so that policy_documents becomes the editable
source of truth the admin UI manages (the files remain as the initial seed).

Idempotent: re-running refreshes each document's row and chunks. SOURCES.md is
skipped. The document title is taken from the first "# " heading, falling back to
the file name — the same rule the original ingestion used.

Usage (repo root, venv active, .env with GEMINI_API_KEY and DATABASE_URL):
    python -m scripts.seed_documents
"""
from __future__ import annotations

import asyncio
import glob
import os

import asyncpg
from dotenv import load_dotenv

from app.kb import upsert_document

load_dotenv()

CORPUS_DIR = os.getenv("CORPUS_DIR", "corpus")


def _doc_title(text: str, filename: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return os.path.splitext(os.path.basename(filename))[0]


async def seed() -> None:
    files = sorted(
        f for f in glob.glob(os.path.join(CORPUS_DIR, "**", "*.md"), recursive=True)
        if os.path.basename(f).lower() != "sources.md"
    )
    if not files:
        print(f"No .md files found under {CORPUS_DIR!r}.")
        return

    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], statement_cache_size=0)
    try:
        total = 0
        for path in files:
            text = open(path, encoding="utf-8").read()
            title = _doc_title(text, path)
            chunks = await upsert_document(pool, title, text)
            total += chunks
            print(f"  {title}: {chunks} chunks")
        print(f"\nSeed complete. {len(files)} documents, {total} chunks in policy_chunks.")
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(seed())