"""
Manual check for the retrieval step (Issue #6). Embeds a few sample passenger
questions, retrieves the most similar policy chunks, and prints the scores so you
can see what the knowledge base returns before it is wired into answering.

Usage (repo root, venv active, .env with GEMINI_API_KEY and DATABASE_URL):
    python -m scripts.try_retrieval
"""
import asyncio
import os

import asyncpg
from dotenv import load_dotenv

from app.retrieval import retrieve

load_dotenv()

QUESTIONS = [
    "What is the baggage allowance for economy class?",
    "Can I bring my dog in the cabin?",
    "When does online check-in close?",
    "Can I carry a pocket knife in my hand luggage?",
    "What is the capital of France?",  # out of scope — scores should be low
]


async def main() -> None:
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], statement_cache_size=0)
    try:
        for q in QUESTIONS:
            results = await retrieve(pool, q, k=3)
            print(f"\nQ: {q}")
            for r in results:
                snippet = " ".join(r["content"].split())[:70]
                print(f"   {r['similarity']:.3f}  [{r['doc_title']}]  {snippet}...")
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
