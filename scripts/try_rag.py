"""
Manual check for the full RAG pipeline with the hallucination gate (Issue #7).
Runs several questions through retrieve -> gate -> generate and prints, for each,
whether it was grounded, the top similarity, the answer, and the sources.

Usage (repo root, venv active, .env with GEMINI_API_KEY and DATABASE_URL):
    python -m scripts.try_rag
"""
import asyncio
import os

import asyncpg
from dotenv import load_dotenv

from app.rag import answer_informational, SIMILARITY_THRESHOLD

load_dotenv()

QUESTIONS = [
    "What is the baggage allowance for economy class?",
    "Can I bring my dog in the cabin?",
    "When does online check-in close for international flights?",
    "Can I carry a pocket knife in my hand luggage?",
    "What is the capital of France?",        # out of scope -> fallback
    "Can I get a refund if my flight is cancelled?",  # not in corpus yet -> likely fallback
]


async def main() -> None:
    print(f"(similarity threshold = {SIMILARITY_THRESHOLD})")
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], statement_cache_size=0)
    try:
        for q in QUESTIONS:
            r = await answer_informational(pool, q)
            tag = r["status"].upper()   # GROUNDED | FALLBACK | UNAVAILABLE
            srcs = ", ".join(sorted({s["doc_title"] for s in r["sources"]})) or "-"
            print(f"\nQ: {q}")
            print(f"   [{tag}] top_similarity={r['top_similarity']:.3f}  sources: {srcs}")
            print(f"   A: {r['reply']}")
            await asyncio.sleep(5)  # pace calls to stay under the free-tier per-minute limit
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())