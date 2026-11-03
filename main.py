import os
import uuid
from contextlib import asynccontextmanager
import asyncio
from app.router import classify
from app.slot_filling import handle_transactional
import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    route: str
    score: float
    session_id: str


load_dotenv()

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

    if route == "transactional":
        tx_result = await handle_transactional(
            pool,
            session_id,
            req.message,
        )
        reply = tx_result["reply"]
    else:
        reply = (
            "This looks like a policy question. "
            "The information assistant that answers these "
            "from Kenya Airways documents is coming in a later sprint."
        )

    return ChatResponse(
        reply=reply,
        route=route,
        score=round(result["score"], 3),
        session_id=session_id,
    )