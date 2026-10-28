-- 001_init.sql
-- Project initialisation: pgvector, plus the first table (bookings) with both walls up.

create extension if not exists vector with schema extensions;

create table public.bookings (
    id              bigint generated always as identity primary key,
    pnr             text not null,
    last_name       text not null,
    first_name      text,
    flight_number   text not null,
    origin          text,
    destination     text,
    departure_time  timestamptz,
    seat            text,
    status          text not null default 'confirmed',
    created_at      timestamptz not null default now(),
    constraint bookings_pnr_format check (pnr ~ '^[A-Z0-9]{6}$'),
    constraint bookings_pnr_last_name_key unique (pnr, last_name)
);

-- Wall 1 (grants): the public API roles get no access to this table.
revoke all on table public.bookings from anon, authenticated;

-- Wall 2 (RLS): even if a grant is added later, no policy means no rows are visible.
alter table public.bookings enable row level security;