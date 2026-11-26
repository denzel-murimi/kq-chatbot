# Kenya Airways Passenger Self-Service Assistant

Final-year project (Strathmore University, BSc Informatics and Computer Science): an intelligent passenger self-service chatbot that combines Retrieval-Augmented Generation (RAG) for policy questions with deterministic, intent-driven slot filling for booking requests.

- Live demo (controlled pilot, synthetic data): https://kq-chatbot.vercel.app
- Backend API: https://kq-chatbot-api-jpoo.onrender.com (`/health`)
- Evaluated release: `v1.0.0`; documentation/fix release: `v1.0.1`

This is an academic prototype. It is not affiliated with Kenya Airways, uses only public policy content and invented bookings, and never connects to any airline system.

## How it works

1. `/chat` checks whether the session has a booking request in progress.
2. Greetings and thanks get a short reply (`app/smalltalk.py`).
3. Follow-up questions are rewritten into standalone questions (`app/contextualize.py`).
4. The semantic router (`app/router.py`) compares the message with labelled example phrases and picks `informational`, `transactional` or `out_of_scope`.
5. Informational messages go to the RAG pipeline (`app/rag.py`). If the best chunk scores below 0.6, a fixed fallback is returned and the language model is not called.
6. Transactional messages go to the slot-filling state machine (`app/slot_filling.py`), which collects the booking reference, surname and seat, asks for confirmation, then calls `app/execution.py`. This is the only module that touches `bookings`.
7. Every request is logged to `query_logs` with per-stage timings.

Stack: Next.js 15 / React 19 / Tailwind 4 (frontend), FastAPI + asyncpg (backend), Supabase PostgreSQL + pgvector, Google `gemini-embedding-001` (1536-d embeddings), Groq `openai/gpt-oss-20b` (generation).

## Repository layout

```
app/                backend modules (router, rag, slot_filling, execution, admin, ...)
app/ingestion/      paragraph-aware chunker and re-indexing
corpus/             17 policy documents + SOURCES.md (URLs and access dates)
db/migrations/      001–007 SQL migrations (run in order)
frontend/           Next.js passenger UI and admin console
scripts/            seeding, component harnesses and evaluation scripts
tests/              router boundary, chunker and contextualizer tests
data/atis/          ATIS test split used only for out-of-domain evaluation
main.py             FastAPI app and /chat orchestration
render.yaml         Render deployment blueprint
```

## Setup

### 1. Database (Supabase)

1. Create a Supabase project. Enable the `vector` extension (Database → Extensions) in the `extensions` schema.
2. In the SQL editor, run `db/migrations/001_init.sql` to `007_query_log_timings.sql` in numeric order. Every table has row-level security on with no policies, and access is revoked from `anon` and `authenticated`.
3. Copy the **transaction pooler** connection string (port 6543) for `DATABASE_URL`.

### 2. Environment variables

Create `.env` in the repository root. It is git-ignored, so never commit it.

```
GEMINI_API_KEY=...
GROQ_API_KEY=...
DATABASE_URL=postgresql://...:6543/postgres
ADMIN_KEY=choose-a-long-random-string
CORS_ORIGINS=http://localhost:3000
# optional
GROQ_MODEL=openai/gpt-oss-20b
RAG_SIMILARITY_THRESHOLD=0.6
```

Frontend: create `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`. Never put `ADMIN_KEY` in a `NEXT_PUBLIC_` variable.

### 3. Backend

```powershell
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m scripts.seed_documents  # loads corpus/ -> 17 documents, 74 chunks
uvicorn main:app --reload
```

### 4. Frontend

```powershell
cd frontend
npm install
npm run dev                       # http://localhost:3000, admin console at /admin
```

## Verify

- `GET http://localhost:8000/health` should return `{"status":"ok"}`.
- `GET http://localhost:8000/db-check` should return the database server time.
- In the chat, ask *"What is the checked baggage allowance in economy?"*. You should get a grounded answer with its source.
- Send *"Change seat RT9K3L Mwangi to 10F"*, then *"yes"*. The seat should change, and the admin console's Bookings tab shows the result.

## Tests and evaluation

Component harnesses and tests run against your database and the model APIs. Each call counts against free-tier quotas, so run them sparingly.

```powershell
python -m scripts.try_retrieval
python -m scripts.try_rag
python -m scripts.try_entities
python -m scripts.try_slot_filling
python -m scripts.try_execution          # restores any seat it changes
python -m scripts.check_rls
python -m tests.test_router_boundary
python -m scripts.try_atis_router        # writes atis_router_results.csv
python -m scripts.eval_intent_classification --set A   # validation set
python -m scripts.eval_intent_classification --set B   # final test set
```

Committed results: `atis_router_results.csv`, `intent_eval_baseline.csv`, `intent_eval_setA.csv`, `intent_eval_setB.csv`.

## Deployment

- **Backend (Render):** create a Blueprint from this repo. `render.yaml` sets Python 3.12.7, region Frankfurt, `pip install -r requirements.txt`, `uvicorn main:app --host 0.0.0.0 --port $PORT` and health check `/health`. Enter the five secrets in the dashboard, and set `CORS_ORIGINS` to the Vercel URL. Deploys from `main`.
- **Frontend (Vercel):** import the repo with root directory `frontend/`, set `NEXT_PUBLIC_API_URL` to the Render URL, and use `main` as the production branch.
- **Rollback:** Render → Events → roll back to a previous deploy. Vercel → Deployments → promote an earlier deployment. Or `git revert` on `main`.

## Branching and releases

Feature branches (`feature/issue-N-...`) merge into `develop` through pull requests. Releases are merged into `main` and tagged (`v0.1.0-milestone-1` … `v1.0.0`, `v1.0.1`). Hosting builds from `main`.
