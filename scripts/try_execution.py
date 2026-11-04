"""
End-to-end test of the transactional pipeline: slot-filling (Issue #9) through
to database execution (Issue #10), against real chat_sessions + bookings tables.

Seed-agnostic and non-destructive: it reads the booking's current values at
runtime and asserts the replies reflect THOSE, rather than assuming particular
seed data. Any seat it changes is restored before the script exits, so it can be
run repeatedly against the same database (including the real Supabase one)
without leaving a mark.

The surname extractor is stubbed (no GROQ_API_KEY / network needed); the regex
extractor and all SQL run for real.

It uses two demo bookings that must exist and share a flight (for the
seat-conflict test). Override the defaults with env vars if yours differ:
    DEMO1_PNR / DEMO1_NAME   (status-check booking; default ABC123 / Doe)
    DEMO2_PNR / DEMO2_NAME   (seat-change booking; default RT9K3L / Mwangi)

Run:
    DATABASE_URL=... PYTHONPATH=. python scripts/try_execution.py
"""
from __future__ import annotations

import asyncio
import os

import asyncpg

import app.slot_filling as sf


def _fake_surname(message: str):
    low = message.lower()
    for cue in ("last name", "surname", "name is", "name"):
        if cue in low:
            after = message[low.index(cue) + len(cue):].strip().split()
            while after and after[0].lower() in ("is", "the", "was"):
                after = after[1:]
            if after:
                return after[0].strip(".,")
    words = message.strip().split()
    if len(words) == 1 and words[0].isalpha():
        return words[0]
    return None


sf.extract_surname = _fake_surname

DEMO1_PNR = os.getenv("DEMO1_PNR", "ABC123")
DEMO1_NAME = os.getenv("DEMO1_NAME", "Doe")
DEMO2_PNR = os.getenv("DEMO2_PNR", "RT9K3L")
DEMO2_NAME = os.getenv("DEMO2_NAME", "Mwangi")

# A seat unlikely to be occupied, used for the successful-change test.
FREE_SEAT = os.getenv("FREE_SEAT", "45K")


def check(label, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL':4} {label}" + (f"  [{detail}]" if detail and not cond else ""))
    return cond


async def main():
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], statement_cache_size=0)
    await pool.execute("truncate chat_sessions")
    ok = True
    restore = None  # (pnr, original_seat) to put back at the end

    try:
        # Read the demo bookings' real values up front; assert against these.
        b1 = await pool.fetchrow(
            "select flight_number, origin, destination, seat, status from bookings "
            "where upper(pnr)=upper($1) and lower(last_name)=lower($2)", DEMO1_PNR, DEMO1_NAME)
        b2 = await pool.fetchrow(
            "select flight_number, departure_time, seat from bookings "
            "where upper(pnr)=upper($1) and lower(last_name)=lower($2)", DEMO2_PNR, DEMO2_NAME)
        if b1 is None or b2 is None:
            print(f"Demo bookings not found ({DEMO1_PNR}/{DEMO1_NAME}, {DEMO2_PNR}/{DEMO2_NAME}). "
                  "Set DEMO*_PNR / DEMO*_NAME to bookings in your table.")
            return

        # 1 — check flight status: reply must echo THIS booking's real values.
        print(f"1 — check flight status ({DEMO1_PNR} / {DEMO1_NAME})")
        r = await sf.handle_transactional(pool, "c1", f"status of booking {DEMO1_PNR}, surname {DEMO1_NAME}")
        ok &= check("found", r["outcome"] == "found", r["reply"])
        ok &= check("reply reflects the booking's real flight/route/status",
                    b1["flight_number"] in r["reply"] and b1["destination"] in r["reply"]
                    and b1["status"] in r["reply"], r["reply"])
        print("     ->", r["reply"])

        # 2 — change to a free seat, collected across turns. Capture the
        #     original seat first so it can be restored at the end.
        print(f"2 — change seat to a free one ({DEMO2_PNR} / {DEMO2_NAME} -> {FREE_SEAT})")
        orig_seat = b2["seat"]
        restore = (DEMO2_PNR, orig_seat)
        await sf.handle_transactional(pool, "c2", "I want to change my seat")
        await sf.handle_transactional(pool, "c2", DEMO2_PNR)
        await sf.handle_transactional(pool, "c2", f"surname {DEMO2_NAME}")
        r = await sf.handle_transactional(pool, "c2", FREE_SEAT)
        ok &= check("seat changed", r["outcome"] == "changed", r["reply"])
        ok &= check("reply confirms real old seat -> new seat",
                    orig_seat in r["reply"] and FREE_SEAT in r["reply"], r["reply"])
        db_seat = await pool.fetchval("select seat from bookings where upper(pnr)=upper($1)", DEMO2_PNR)
        ok &= check(f"bookings row actually updated to {FREE_SEAT}", db_seat == FREE_SEAT, f"db={db_seat}")
        print("     ->", r["reply"])

        # 3 — requested seat already taken: try to take demo1's seat, which is
        #     on the same flight. Only meaningful if they share a flight.
        same_flight = (b1["flight_number"] == b2["flight_number"])
        if same_flight:
            print(f"3 — requested seat already taken (-> {b1['seat']}, held on {b1['flight_number']})")
            r = await sf.handle_transactional(
                pool, "c3", f"change seat, PNR {DEMO2_PNR}, last name {DEMO2_NAME}, to {b1['seat']}")
            ok &= check("refused as taken", r["outcome"] == "seat_taken", r["reply"])
            db_seat = await pool.fetchval("select seat from bookings where upper(pnr)=upper($1)", DEMO2_PNR)
            ok &= check(f"seat unchanged after refusal (still {FREE_SEAT})", db_seat == FREE_SEAT, f"db={db_seat}")
            print("     ->", r["reply"])
        else:
            print("3 — skipped (demo bookings are on different flights)")

        # 4 — already in the requested seat (demo2 is now in FREE_SEAT).
        print(f"4 — already in requested seat ({DEMO2_PNR} -> {FREE_SEAT} again)")
        r = await sf.handle_transactional(
            pool, "c4", f"change seat PNR {DEMO2_PNR} surname {DEMO2_NAME} to {FREE_SEAT}")
        ok &= check("no-change reported", r["outcome"] == "no_change", r["reply"])
        print("     ->", r["reply"])

        # 5 — booking not found.
        print("5 — booking not found (ZZ9999 / Nobody)")
        r = await sf.handle_transactional(pool, "c5", "status of booking ZZ9999 surname Nobody")
        ok &= check("friendly not-found, not an error", r["outcome"] == "not_found", r["reply"])
        print("     ->", r["reply"])

        # 6 — surname case-insensitive.
        print(f"6 — surname case-insensitive ({DEMO1_PNR} / {DEMO1_NAME.lower()})")
        r = await sf.handle_transactional(pool, "c6", f"status booking {DEMO1_PNR} surname {DEMO1_NAME.lower()}")
        ok &= check("lowercase surname still matches", r["outcome"] == "found", r["reply"])

    finally:
        # Put the seat back exactly as it was — non-destructive.
        if restore is not None:
            await pool.execute("update bookings set seat=$1 where upper(pnr)=upper($2)", restore[1], restore[0])
            print(f"\n(restored {restore[0]} seat to {restore[1]})")
        await pool.close()

    print("\n" + ("ALL PASS" if ok else "SOME FAILED"))


if __name__ == "__main__":
    asyncio.run(main())