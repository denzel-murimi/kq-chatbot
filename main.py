import os
import uuid
from contextlib import asynccontextmanager
import asyncio

from dotenv import load_dotenv

# Load .env before importing app modules: some read settings (e.g. GROQ_MODEL) at import time.
load_dotenv()

from app.router import classify
from app.slot_filling import handle_transactional, has_pending_request
from app.rag import answer_informational
import asyncpg
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


OUT_OF_SCOPE_REPLY = (
    "I can help with Kenya Airways travel policies (baggage, check-in, prohibited "
    "items and travelling with pets) and with your booking: flight status and seat "
    "changes. I can't help with that one, but ask me anything in those areas."
)

# While the bot is waiting for a booking detail, a short reply such as a bare
# surname ("Otieno") carries almost no meaning for the router and can land in any
# class. Such replies stay with slot-filling; only a clear policy question
# (informational at or above this score) is answered from the documents instead.
# Real policy questions scored 0.82-0.96 in testing; bare surnames about 0.70.
MIDFLOW_INFORMATIONAL_MIN_SCORE = 0.8


class ChatResponse(BaseModel):
    reply: str
    route: str
    score: float
    session_id: str
    grounded: bool = False
    # Deduplicated document titles, only for grounded informational answers.
    sources: list[str] = []


pool: asyncpg.Pool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=5, statement_cache_size=0)
    yield
    await pool.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/db-check")
async def db_check():
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "select now() as server_time"
        )

    return {
        "connected": True,
        "server_time": str(row["server_time"]),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = await asyncio.to_thread(
        classify,
        req.message,
    )

    route = result["route"]
    session_id = req.session_id or str(uuid.uuid4())

    if route != "transactional" and await has_pending_request(pool, session_id):
        clear_policy_question = (
            route == "informational"
            and result["score"] >= MIDFLOW_INFORMATIONAL_MIN_SCORE
        )
        if not clear_policy_question:
            route = "transactional"

    grounded = False
    sources: list[str] = []

    if route == "transactional":
        tx_result = await handle_transactional(
            pool,
            session_id,
            req.message,
        )
        reply = tx_result["reply"]
    elif route == "out_of_scope":
        reply = OUT_OF_SCOPE_REPLY
    else:
        # reply already holds the right text for every case: grounded answer,
        # hallucination fallback, or "service busy".
        info = await answer_informational(pool, req.message)
        reply = info["reply"]
        grounded = info["grounded"]
        # Several chunks often come from one document; passengers see each title once, no scores.
        for s in info["sources"]:
            if s["doc_title"] not in sources:
                sources.append(s["doc_title"])

    return ChatResponse(
        reply=reply,
        route=route,
        score=round(result["score"], 3),
        session_id=session_id,
        grounded=grounded,
        sources=sources,
    )
