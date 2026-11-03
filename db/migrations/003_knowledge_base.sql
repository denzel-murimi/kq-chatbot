-- 003_knowledge_base.sql
-- Knowledge base for the RAG pipeline. Stores chunked Kenya Airways policy text
-- and its embedding. Same two-wall access control as the bookings table.
--
-- The pgvector extension was enabled in 001_init.sql into the "extensions"
-- schema, so the vector type is referenced as extensions.vector.

create table public.policy_chunks (
    id          bigint generated always as identity primary key,
    doc_title   text not null,
    content     text not null,
    embedding   extensions.vector(1536) not null,  -- Gemini gemini-embedding-001 @ output_dimensionality=1536
    created_at  timestamptz not null default now()
);

-- Wall 1 (grants): the public API roles get no access.
revoke all on table public.policy_chunks from anon, authenticated;

-- Wall 2 (RLS): enabled with no policies -> no rows exposed via the data API.
alter table public.policy_chunks enable row level security;

-- Vector index: add once the corpus holds a few hundred chunks. Until then a
-- sequential scan over a small table is faster than an index build. Cosine
-- distance (<=>) is used by the retrieval query, so the index uses cosine ops.
-- create index on public.policy_chunks
--   using ivfflat (embedding extensions.vector_cosine_ops) with (lists = 100);