-- 004_sessions.sql
-- Conversational state for the transactional (slot-filling) pipeline. When a
-- passenger starts an action (e.g. "change my seat") but has not yet supplied
-- everything needed, the half-finished request is stored here against their
-- session so the next message can continue it. Same two-wall access control as
-- the other tables.

create table public.chat_sessions (
    session_id  text primary key,
    intent      text,                                   -- e.g. 'change_seat', 'check_flight_status'
    slots       jsonb not null default '{}'::jsonb,      -- collected values so far
    status      text  not null default 'idle',           -- idle | collecting | ready | completed
    updated_at  timestamptz not null default now()
);

-- Wall 1 (grants): the public API roles get no access.
revoke all on table public.chat_sessions from anon, authenticated;

-- Wall 2 (RLS): enabled with no policies -> no rows exposed via the data API.
alter table public.chat_sessions enable row level security;