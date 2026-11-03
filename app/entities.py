"""
Entity extraction for the transactional pipeline (Issue #8).

Hybrid approach:
  - Regex for the clearly-shaped fields: PNR (6 alphanumeric with a digit),
    seat (e.g. 14C) and flight number (KQ + digits). These are deterministic,
    instant and fully explainable.
  - A constrained Groq call for the free-text surname, which has no fixed shape.

The language model is used ONLY to read a value out of the text. It never
decides what to do with a booking — that is the state machine's job (Issue #9).
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

    # Flight number first (so a flight like KQ1000 is not mistaken for a PNR).
    flight = _FLIGHT_RE.search(message)
    if flight:
        slots["flight_number"] = "KQ " + flight.group(1)

    # PNR: a 6-character alphanumeric token containing at least one digit. The
    # digit requirement avoids matching plain six-letter words (LONDON, ECONOMY
    # is 7 so already excluded), and KQ-flight tokens are skipped explicitly.
    for tok in _PNR_RE.findall(upper):
        if tok.startswith("KQ") and tok[2:].isdigit():
            continue  # that's a flight number, not a PNR
        if any(ch.isdigit() for ch in tok):
            slots["pnr"] = tok
            break

    # Seat: one or two digits then a cabin letter (14C).
    seat = _SEAT_RE.search(message)
    if seat:
        slots["seat_number"] = seat.group(1).upper()

    return slots


@lru_cache(maxsize=1)
def _client() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def extract_surname(message: str) -> str | None:
    """Ask the model to read out the passenger surname, if present. Returns the
    surname or None. Extraction only — the model makes no decisions."""
    resp = _client().chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content":
                "You extract the passenger's surname (last name) from the message. "
                "Reply with ONLY the surname as a single word and nothing else. "
                "If no surname is present, reply exactly: NONE"},
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
