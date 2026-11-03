"""
Exercise the slot-filling state machine (Issue #9) against a real chat_sessions
table. The surname extractor is stubbed to a simple rule so the test needs no
GROQ_API_KEY or network; the regex extractor (extract_structured) runs for real.
What is being verified is the STATE MACHINE: slot collection turn by turn,
persistence across turns, both intents, and reaching 'ready'.

Run (local Postgres with a chat_sessions table):
    DATABASE_URL=postgresql://postgres@127.0.0.1/sftest python scripts/try_slot_filling.py
"""
from __future__ import annotations

import asyncio
import os

import asyncpg

import app.slot_filling as sf


# --- stub the surname extractor (stand-in for the Groq call) ----------------
# Rule: if the message contains a cue word, take the word after it; if the whole
# message is a single alphabetic word, treat it as the name. Mirrors what the
# real model does on the cued/standalone cases, with no network.
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


sf.extract_surname = _fake_surname  # patch the name the module calls


def check(label, cond):
    print(f"  {'PASS' if cond else 'FAIL':4} {label}")
    return cond


async def main():
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], statement_cache_size=0)
    await pool.execute("truncate chat_sessions")
    ok = True
    try:
        # --- Scenario 1: change_seat, one slot per turn --------------------
        print("Scenario 1 — change_seat, collected across turns (session s1)")
        r = await sf.handle_transactional(pool, "s1", "I want to change my seat")
        ok &= check("asks for PNR first", r["status"] == "collecting" and "PNR" in r["reply"])
        ok &= check("intent locked to change_seat", r["intent"] == "change_seat")

        r = await sf.handle_transactional(pool, "s1", "RT9K3L")
        ok &= check("PNR captured, now asks last name", r["slots"].get("pnr") == "RT9K3L" and "last name" in r["reply"].lower())

        r = await sf.handle_transactional(pool, "s1", "my last name is Mwangi")
        ok &= check("surname captured, now asks seat", r["slots"].get("last_name") == "Mwangi" and "seat" in r["reply"].lower())

        r = await sf.handle_transactional(pool, "s1", "14C")
        ok &= check("seat captured -> ready", r["status"] == "ready" and r["slots"].get("seat_number") == "14C")
        ok &= check("ready reply names all three slots",
                    all(v in r["reply"] for v in ("RT9K3L", "Mwangi", "14C")))

        # persisted?
        row = await pool.fetchrow("select status, slots from chat_sessions where session_id='s1'")
        ok &= check("row persisted as ready", row["status"] == "ready")

        # --- Scenario 2: check_flight_status ------------------------------
        print("Scenario 2 — check_flight_status (session s2)")
        r = await sf.handle_transactional(pool, "s2", "what's the status of my flight")
        ok &= check("status intent chosen", r["intent"] == "check_flight_status")
        ok &= check("asks PNR (seat never requested for this intent)", "PNR" in r["reply"])

        r = await sf.handle_transactional(pool, "s2", "ABC123")
        ok &= check("asks last name", "last name" in r["reply"].lower())
        r = await sf.handle_transactional(pool, "s2", "Doe")
        ok &= check("two slots -> ready (no seat asked)", r["status"] == "ready" and "seat_number" not in r["slots"])

        # --- Scenario 3: everything in one message ------------------------
        print("Scenario 3 — all details in the first message (session s3)")
        r = await sf.handle_transactional(pool, "s3", "change my seat to 14C, booking RT9K3L, surname Mwangi")
        ok &= check("ready immediately", r["status"] == "ready")
        ok &= check("all three slots filled",
                    r["slots"].get("pnr") == "RT9K3L" and r["slots"].get("last_name") == "Mwangi"
                    and r["slots"].get("seat_number") == "14C")

        # --- Scenario 4: idempotency / resuming a fresh session -----------
        print("Scenario 4 — session isolation")
        rows = await pool.fetch("select session_id from chat_sessions order by session_id")
        ok &= check("three independent sessions stored", [x["session_id"] for x in rows] == ["s1", "s2", "s3"])
    finally:
        await pool.close()

    print("\n" + ("ALL PASS" if ok else "SOME FAILED"))


if __name__ == "__main__":
    asyncio.run(main())