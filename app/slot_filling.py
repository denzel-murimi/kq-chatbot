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
import re

from app.entities import extract_structured, extract_surname
from app.execution import execute_transaction, preview_seat_change

INTENT_SLOTS = {
    "check_flight_status": ["pnr", "last_name"],
    "change_seat": ["pnr", "last_name", "seat_number"],
}

SLOT_PROMPTS = {
    "pnr": "Sure — what's your 6-character booking reference (PNR)?",
    "last_name": "Thanks. And the last name on the booking?",
    "seat_number": "Which seat would you like? For example, 14C.",
}

_CANCEL = {
    "cancel",
    "start over",
    "restart",
    "never mind",
    "nevermind",
    "forget it",
    "stop",
}

# Answers to "Would you like me to proceed?" before a seat change is written.
_YES = {"yes", "y", "yeah", "yep", "yes please", "proceed", "confirm", "go ahead",
        "ok", "okay", "sure", "do it"}
_NO = {"no", "n", "nope", "no thanks", "no thank you", "dont", "do not"}


# One word of letters, allowing an inner hyphen or apostrophe (Wa-Njeri, O'Neil).
_SURNAME_TOKEN = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")


def _norm(message: str) -> str:
    """Lower-case and drop punctuation, so "Yes!" and "Don't." match."""
    return re.sub(r"[^a-z0-9\s]", "", message.lower()).strip()

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
    the bot has just asked for a missing detail or for confirmation. Read-only:
    never creates a row."""
    status = await db.fetchval(
        "select status from chat_sessions where session_id = $1", session_id
    )
    return status in ("collecting", "confirming")


async def _save(db, session_id: str, intent: str, slots: dict, status: str) -> None:
    await db.execute(
        "update chat_sessions set intent = $1, slots = $2::jsonb, status = $3, "
        "updated_at = now() where session_id = $4",
        intent, json.dumps(slots), status, session_id,
    )


async def clear_session(db, session_id: str) -> None:
    """Drop any in-progress request so the next message starts fresh."""
    await db.execute(
        "update chat_sessions set intent = null, slots = '{}'::jsonb, status = 'idle', "
        "updated_at = now() where session_id = $1",
        session_id,
    )


async def handle_transactional(db, session_id: str, message: str) -> dict:
    """Advance the slot-filling conversation one turn. Returns a dict with the
    reply, the status ('collecting' | 'confirming' | 'done' | 'idle'), the intent
    and the slots."""
    text = _norm(message)

    # Let the user abandon a half-finished request ("cancel", "start over!").
    if text in _CANCEL:
        await clear_session(db, session_id)
        return {"reply": "I've cancelled the current request. How else can I help?",
                "status": "idle", "intent": None, "slots": {}}

    session = await _get_session(db, session_id)

    # A seat change is waiting for the passenger's yes/no.
    if session["status"] == "confirming" and session["intent"]:
        intent = session["intent"]
        slots = dict(session["slots"])
        if text in _YES:
            # Only now is the booking written.
            result = await execute_transaction(db, intent, slots)
            await _save(db, session_id, intent, slots, "done")
            return {"reply": result["reply"], "status": "done", "intent": intent,
                    "slots": slots, "outcome": result["outcome"]}
        if text in _NO:
            await clear_session(db, session_id)
            return {"reply": "Okay, I've cancelled the seat change.", "status": "idle",
                    "intent": None, "slots": {}}
        # A different seat ("actually 15D") replaces the pending one and is
        # confirmed afresh; anything else just repeats the question.
        new_seat = extract_structured(message).get("seat_number")
        if not new_seat:
            return {"reply": "Please reply yes to go ahead with the seat change, or no to cancel it.",
                    "status": "confirming", "intent": intent, "slots": slots}
        slots["seat_number"] = new_seat
        return await _finish_slots(db, session_id, intent, slots)

    # Continue an in-progress request; otherwise start a new one.
    asked_for = None
    if session["status"] == "collecting" and session["intent"]:
        intent = session["intent"]
        slots = dict(session["slots"])
        # The slot the bot's last prompt asked for: the first one still missing.
        asked_for = next((s for s in INTENT_SLOTS[intent] if s not in slots), None)
    else:
        intent = classify_transactional_intent(message)
        slots = {}

    # Extract whatever this message supplies. Structured fields are free; the
    # surname costs one model call, so only ask for it when it is still needed.
    slots.update(extract_structured(message))
    required = INTENT_SLOTS[intent]

    # Passengers answer "And the last name on the booking?" with just the name
    # ("Were"). A single word given straight after that prompt is the surname,
    # so take it as-is rather than asking the model, which can reject a short
    # name that is also an English word.
    if asked_for == "last_name" and "last_name" not in slots:
        single = message.strip().strip(".,!")
        if _SURNAME_TOKEN.fullmatch(single):
            slots["last_name"] = single

    if "last_name" in required and "last_name" not in slots:
        name = await asyncio.to_thread(extract_surname, message)
        if name:
            slots["last_name"] = name

    missing = [s for s in required if s not in slots]

    if missing:
        await _save(db, session_id, intent, slots, "collecting")
        return {"reply": SLOT_PROMPTS[missing[0]], "status": "collecting",
                "intent": intent, "slots": slots}

    return await _finish_slots(db, session_id, intent, slots)


async def _finish_slots(db, session_id: str, intent: str, slots: dict) -> dict:
    """Every slot is present. A seat change is a write, so it is checked and
    described to the passenger first and only runs after they say yes; a status
    check is read-only and runs straight away."""
    if intent == "change_seat":
        preview = await preview_seat_change(db, slots)
        if preview["outcome"] == "confirm":
            await _save(db, session_id, intent, slots, "confirming")
            return {"reply": preview["reply"], "status": "confirming", "intent": intent,
                    "slots": slots}
        # Refused (booking not found, seat taken, same seat): nothing to confirm.
        await _save(db, session_id, intent, slots, "done")
        return {"reply": preview["reply"], "status": "done", "intent": intent,
                "slots": slots, "outcome": preview["outcome"]}

    # Execute against the bookings table (Issue #10). The session is marked
    # 'done' so the next message starts a fresh request rather than resuming it.
    result = await execute_transaction(db, intent, slots)
    await _save(db, session_id, intent, slots, "done")
    return {"reply": result["reply"], "status": "done", "intent": intent,
            "slots": slots, "outcome": result["outcome"]}