import os
import uuid
from contextlib import asynccontextmanager
import asyncio
import time

from app import analytics
from app.timing import StageTimer
from dotenv import load_dotenv

# Load .env before importing app modules: some read settings (e.g. GROQ_MODEL) at import time.
load_dotenv()

from app.router import classify
from app.contextualize import contextualize
from app.slot_filling import handle_transactional, has_pending_request
from app.rag import answer_informational
import asyncpg
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from app.smalltalk import detect as detect_smalltalk
from app.admin import router as admin_router

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    # Prior turns ({"role": "user" | "bot", "text": ...}) so a follow-up such as
    # "where can I find that form?" can be rewritten into a standalone question.
    history: list[dict] = []


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
    app.state.pool = pool  # admin routes read the pool from here
    yield
    await pool.close()


app = FastAPI(lifespan=lifespan)
app.include_router(admin_router)




_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip()
        for o in _origins
    ],
    allow_credentials=True,
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
    t0 = time.perf_counter()
    timer = StageTimer()
    session_id = req.session_id or str(uuid.uuid4())
    pending = await has_pending_request(pool, session_id)

    # Pleasantries are answered before the router runs: cheaper, and the
    # embedding router tends to misfile them as out-of-scope. Skipped mid-request,
    # where e.g. "no thanks" is the answer to "Would you like me to proceed?".
    smalltalk_reply = None if pending else detect_smalltalk(req.message)
    if smalltalk_reply is not None:
        await analytics.log_query(
            pool,
            session_id=session_id,
            route="smalltalk",
            message=req.message,
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )
        return ChatResponse(
            reply=smalltalk_reply,
            route="smalltalk",
            score=1.0,
            session_id=session_id,
        )

    # Rewrite follow-ups into standalone questions before routing. Skipped while a
    # transaction is mid-flow: a bare PNR or "yes" must reach slot-filling as typed.
    # contextualize is best-effort and falls back to the original message.
    if pending:
        query = req.message
    else:
        with timer.track("contextualize"):
            query = await asyncio.to_thread(contextualize, req.message, req.history)

    with timer.track("classify"):
        result = await asyncio.to_thread(
            classify,
            query,
        )
    route = result["route"]

    if route != "transactional" and pending:
        clear_policy_question = (
            route == "informational"
            and result["score"] >= MIDFLOW_INFORMATIONAL_MIN_SCORE
        )
        if not clear_policy_question:
            route = "transactional"

    grounded = False
    sources: list[str] = []
    top_similarity: float | None = None
    outcome: str | None = None

    if route == "transactional":
        with timer.track("transactional"):
            tx_result = await handle_transactional(
                pool,
                session_id,
                query,
            )
        outcome = tx_result.get("outcome")
        reply = tx_result["reply"]
    elif route == "out_of_scope":
        reply = OUT_OF_SCOPE_REPLY
    else:
        # reply already holds the right text for every case: grounded answer,
        # hallucination fallback, or "service busy".
        with timer.track("informational"):
            info = await answer_informational(pool, query)
        timer.merge(info.get("timings"))
        reply = info["reply"]
        grounded = info["grounded"]
        top_similarity = info["top_similarity"]
        # Several chunks often come from one document; passengers see each title once, no scores.
        for s in info["sources"]:
            if s["doc_title"] not in sources:
                sources.append(s["doc_title"])

    latency_ms = int((time.perf_counter() - t0) * 1000)

    await analytics.log_query(
        pool,
        session_id=session_id,
        route=route,
        message=req.message,
        latency_ms=latency_ms,
        grounded=grounded,
        top_similarity=top_similarity,
        outcome=outcome,
        timings=timer.as_dict(),
    )

    return ChatResponse(
        reply=reply,
        route=route,
        score=round(result["score"], 3),
        session_id=session_id,
        grounded=grounded,
        sources=sources,
    )
