-- 005_policy_documents.sql
-- The editable SOURCE text of the knowledge base.
--
-- policy_chunks holds the embedded INDEX used for retrieval. This table holds
-- the original document text that an administrator manages through the admin
-- UI. Editing a document here and re-indexing regenerates that document's rows
-- in policy_chunks, so the knowledge base becomes operational (editable at
-- runtime) rather than a one-shot load from corpus/*.md files.
--
-- The existing corpus/*.md files are loaded into this table once as the initial
-- seed (see scripts/seed_documents.py), after which this table is the source of
-- truth and the files are just the starting point.

create table if not exists public.policy_documents (
    id          bigint generated always as identity primary key,
    title       text        not null unique,   -- matches policy_chunks.doc_title
    content     text        not null,
    updated_at  timestamptz not null default now()
);

-- Two-wall security, identical to bookings and policy_chunks: the anon and
-- authenticated roles get no direct access, and RLS is enabled with no policies.
-- The backend connects as postgres (which has bypassrls) and is the only way in.
revoke all on public.policy_documents from anon, authenticated;
alter table public.policy_documents enable row level security;