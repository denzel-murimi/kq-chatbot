"""
Proves the two walls around public.bookings, then leaves no trace.

Wall 1 = table grants (can the role touch the table at all?)
Wall 2 = row level security (which rows may it see or write?)

Everything runs inside one transaction that is rolled back at the end.
Usage (repo root, venv active, DATABASE_URL in .env):  python scripts/check_rls.py
"""
import asyncio
import os
import sys

import asyncpg
from dotenv import load_dotenv

load_dotenv()

PUBLIC_ROLES = ("anon", "authenticated")
PROBE_PNRS = {"anon": "ANON01", "authenticated": "AUTH01"}  # one per role, so attempts never collide
BACKEND_PNR = "ZZZ999"

COUNT = "select count(*) from public.bookings"
INSERT = (
    "insert into public.bookings (pnr, last_name, flight_number) "
    "values ($1, 'Intruder', 'KQ000') returning id"
)

failures: list[str] = []


def check(label: str, ok: bool, detail: str) -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}")
    if not ok:
        failures.append(label)


async def as_role(conn: asyncpg.Connection, role: str, sql: str, *args):
    """Run one statement as `role`. Returns (status, value or message)."""
    await conn.execute(f"set role {role}")  # if this fails it is a setup problem, so let it crash loudly
    try:
        async with conn.transaction():  # a savepoint: a failed statement must not poison the outer transaction
            return "ok", await conn.fetchval(sql, *args)
    except asyncpg.InsufficientPrivilegeError as e:
        return "blocked", str(e)
    except asyncpg.PostgresError as e:
        return "error", f"{type(e).__name__}: {e}"
    finally:
        await conn.execute("reset role")


async def main() -> None:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    me = await conn.fetchrow(
        "select current_user as name, rolsuper, rolbypassrls from pg_roles where rolname = current_user"
    )
    print(f"Connected as {me['name']} (superuser={me['rolsuper']}, bypassrls={me['rolbypassrls']})\n")

    tx = conn.transaction()
    await tx.start()
    try:
        # The backend's own role: this is the connection FastAPI uses.
        await conn.execute(
            "insert into public.bookings (pnr, last_name, flight_number) values ($1, 'Probe', 'KQ000')",
            BACKEND_PNR,
        )
        backend_rows = await conn.fetchval(COUNT)
        check("backend role can read and write", backend_rows >= 1, f"sees {backend_rows} row(s)")

        # Wall 1 on its own: the public API roles have no grants.
        for role in PUBLIC_ROLES:
            status, detail = await as_role(conn, role, COUNT)
            check(
                f"{role} SELECT (grants wall)",
                status == "blocked",
                f"saw {detail} row(s)" if status == "ok" else detail,
            )

        # Open wall 1 on purpose so RLS is the only thing left. Rolled back with everything else.
        await conn.execute("grant select, insert on public.bookings to anon, authenticated")
        for role in PUBLIC_ROLES:
            status, detail = await as_role(conn, role, COUNT)
            check(
                f"{role} SELECT (RLS wall)",
                status == "ok" and detail == 0,
                f"saw {detail} row(s) while the backend sees {backend_rows}" if status == "ok" else detail,
            )
            status, detail = await as_role(conn, role, INSERT, PROBE_PNRS[role])
            check(
                f"{role} INSERT (RLS wall)",
                status == "blocked" and "row-level security" in detail,
                "the insert went through" if status == "ok" else detail,
            )
    finally:
        await tx.rollback()

    left = await conn.fetchval(
        "select count(*) from public.bookings where pnr = any($1::text[])",
        [BACKEND_PNR, *PROBE_PNRS.values()],
    )
    check("no trace left behind", left == 0, f"{left} probe row(s) remain")
    await conn.close()

    if failures:
        print(f"\n{len(failures)} check(s) FAILED: {', '.join(failures)}")
        sys.exit(1)
    print("\nBoth walls hold.")


asyncio.run(main())