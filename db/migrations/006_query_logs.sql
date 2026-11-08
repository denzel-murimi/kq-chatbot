-- 006_query_logs.sql
-- One row per /chat request.
--
-- Dual purpose: it powers the admin monitoring dashboard, and it is the
-- measurement source for the Chapter 5 evaluation (end-to-end latency against
-- the <3s NFR, grounded-vs-fallback rate against the 0% hallucination target,
-- and the route distribution) and for the 50-passenger UAT.
--
-- Nullable columns are only meaningful for some routes: grounded/top_similarity
-- apply to informational queries; outcome carries the transactional result
-- (found / changed / seat_taken / not_found / ...) or the RAG status otherwise.

create table if not exists public.query_logs (
    id             bigint       generated always as identity primary key,
    created_at     timestamptz  not null default now(),
    session_id     text,
    route          text         not null,   -- informational | transactional | out_of_scope | smalltalk
    message        text         not null,
    grounded       boolean,                 -- informational only; null otherwise
    top_similarity real,                     -- informational only
    outcome        text,                     -- transactional outcome, or RAG status
    latency_ms     integer      not null
);

create index if not exists query_logs_created_at_idx on public.query_logs (created_at desc);
create index if not exists query_logs_route_idx      on public.query_logs (route);

revoke all on public.query_logs from anon, authenticated;
alter table public.query_logs enable row level security;