"""
Entity extraction for the transactional pipeline (Issue #8), hybrid approach.
Regex for clearly-shaped fields (PNR, seat, flight); a constrained Groq call for
the free-text surname. The language model only READS a value; it never decides
what to do with a booking.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

from groq import Groq

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

_PNR_RE = re.compile(r"\b[A-Z0-9]{6}\b")
_SEAT_RE = re.compile(r"\b(\d{1,2}[A-K])\b", re.IGNORECASE)
_FLIGHT_RE = re.compile(r"\bKQ\s?(\d{1,4})\b", re.IGNORECASE)


def extract_structured(message: str) -> dict:
    """Regex-only extraction of the clearly-shaped fields. No model call."""
    slots: dict[str, str] = {}
    upper = message.upper()

    flight = _FLIGHT_RE.search(message)
    if flight:
        slots["flight_number"] = "KQ " + flight.group(1)

    for tok in _PNR_RE.findall(upper):
        if tok.startswith("KQ") and tok[2:].isdigit():
            continue  # flight number, not a PNR
        if any(ch.isdigit() for ch in tok):
            slots["pnr"] = tok
            break

    seat = _SEAT_RE.search(message)
    if seat:
        slots["seat_number"] = seat.group(1).upper()

    return slots


@lru_cache(maxsize=1)
def _client() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def extract_surname(message: str) -> str | None:
    """Read out the passenger surname used to look up a booking, if present.
    Extraction only — the model makes no decisions."""
    resp = _client().chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content":
                "You extract the passenger's last name (surname) from the message, "
                "used to look up their booking. The name may be introduced by words "
                "like 'surname', 'last name' or 'name is', or given on its own. If a "
                "full name is given, return only the last word. Reply with ONLY the "
                "name as a single word, or exactly NONE if the message contains no "
                "personal name."},
            {"role": "user", "content": message},
        ],
        temperature=0.0,
        reasoning_effort="low",
        reasoning_format="parsed",
        max_completion_tokens=256,
    )
    out = (resp.choices[0].message.content or "").strip()
    if not out or out.upper() == "NONE":
        return None
    name = re.split(r"\s+", out)[0].strip(".,;:'\"()")
    return name or None