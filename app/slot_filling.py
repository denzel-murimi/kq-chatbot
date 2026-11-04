"""
Slot-filling state machine for the transactional pipeline (Issue #9).

Deterministic by design: this module decides which details are still needed and
when a transaction is ready to execute. The language model only extracts
entities (app/entities.py); it never decides to act on a booking. Conversation
state persists per session in the chat_sessions table, so a request can be
completed across several messages.

Two intents are supported:
  check_flight_status -> needs pnr + last_name
  change_seat         -> needs pnr + last_name + seat_number
"""
from __future__ import annotations

import asyncio
import json

from app.entities import extract_structured, extract_surname
from app.execution import execute_transaction

INTENT_SLOTS = {
    "check_flight_status": ["pnr", "last_name"],
    "change_seat": ["pnr", "last_name", "seat_number"],
}

SLOT_PROMPTS = {
    "pnr": "Sure — what's your 6-character booking reference (PNR)?",
    "last_name": "Thanks. And the last name on the booking?",
    "seat_number": "Which seat would you like? For example, 14C.",
}

INTENT_LABELS = {
    "check_flight_status": "check your flight status",
    "change_seat": "change your seat",
}


def classify_transactional_intent(message: str) -> str:
    """Pick the specific transactional intent. Deterministic keyword rule: a
    mention of a seat is a seat change, otherwise it is a status check."""
    return "change_seat" if "seat" in message.lower() else "check_flight_status"


async def _get_session(db, session_id: str) -> dict:
    row = await db.fetchrow(
        "select intent, slots, status from chat_sessions where session_id = $1", session_id
    )
    if row is None:
        await db.execute(
            "insert into chat_sessions (session_id, intent, slots, status) "
            "values ($1, null, '{}'::jsonb, 'idle')",
            session_id,
        )
        return {"intent": None, "slots": {}, "status": "idle"}
    raw = row["slots"]
    slots = json.loads(raw) if isinstance(raw, str) else dict(raw or {})
    return {"intent": row["intent"], "slots": slots, "status": row["status"]}


async def has_pending_request(db, session_id: str) -> bool:
    """True while this session is part-way through a transactional request, i.e.
    the bot has just asked for a missing detail. Read-only: never creates a row."""
    status = await db.fetchval(
        "select status from chat_sessions where session_id = $1", session_id
    )
    return status == "collecting"


async def _save(db, session_id: str, intent: str, slots: dict, status: str) -> None:
    await db.execute(
        "update chat_sessions set intent = $1, slots = $2::jsonb, status = $3, "
        "updated_at = now() where session_id = $4",
        intent, json.dumps(slots), status, session_id,
    )


async def handle_transactional(db, session_id: str, message: str) -> dict:
    """Advance the slot-filling conversation one turn. Returns a dict with the
    reply, the status ('collecting' | 'ready'), the intent and the slots."""
    session = await _get_session(db, session_id)

    # Continue an in-progress request; otherwise start a new one.
    if session["status"] == "collecting" and session["intent"]:
        intent = session["intent"]
        slots = dict(session["slots"])
    else:
        intent = classify_transactional_intent(message)
        slots = {}

    # Extract whatever this message supplies. Structured fields are free; the
    # surname costs one model call, so only ask for it when it is still needed.
    slots.update(extract_structured(message))
    required = INTENT_SLOTS[intent]
    if "last_name" in required and "last_name" not in slots:
        name = await asyncio.to_thread(extract_surname, message)
        if name:
            slots["last_name"] = name

    missing = [s for s in required if s not in slots]

    if missing:
        await _save(db, session_id, intent, slots, "collecting")
        return {"reply": SLOT_PROMPTS[missing[0]], "status": "collecting",
                "intent": intent, "slots": slots}

    # All slots present: execute the transaction against the bookings table
    # (Issue #10). The session is marked 'done' so the next message starts a
    # fresh request rather than resuming this one.
    result = await execute_transaction(db, intent, slots)
    await _save(db, session_id, intent, slots, "done")
    return {"reply": result["reply"], "status": "done", "intent": intent,
            "slots": slots, "outcome": result["outcome"]}