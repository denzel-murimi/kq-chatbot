"""
History-aware query contextualization for the informational path (refinement).

A follow-up such as "where do I find that form?" has no standalone meaning, so
routing and retrieval both fail on it. This module rewrites the passenger's
latest message into a self-contained question using the recent conversation,
so that the rewritten query names what the passenger actually means
("...the Unaccompanied Minor Form?") and can be routed and retrieved correctly.

Usage rules:
  * Call it BEFORE routing, so the router and retrieval see the standalone query.
  * Skip it while a transactional slot-filling session is active, so a slot
    answer like "14C" is never rewritten (continue that session as-is instead).
  * Use the rewritten query for routing and retrieval; keep the original message
    for logging and display.

It is best-effort: with no usable history, or on any error, or on an empty or
implausible result, it returns the original message unchanged, so it can never
block a reply. The language model only rewrites the question; it never answers.
"""
from __future__ import annotations

import os
from functools import lru_cache

from groq import Groq

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
MAX_HISTORY = 6       # most recent messages considered
MAX_REWRITE_CHARS = 400

SYSTEM_INSTRUCTION = (
    "You rewrite the passenger's latest message into a standalone question for a "
    "Kenya Airways passenger assistant, using the conversation so far. Resolve "
    "references such as 'that form', 'it', 'there' or 'the second one' into "
    "explicit terms drawn from the history. If the latest message is already "
    "self-contained, return it unchanged. Do not answer it and do not add "
    "anything. Reply with ONLY the rewritten question."
)


@lru_cache(maxsize=1)
def _client() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def _format_history(history: list[dict]) -> str:
    lines = []
    for turn in history[-MAX_HISTORY:]:
        text = (turn.get("text") or "").strip()
        if not text:
            continue
        role = "Passenger" if turn.get("role") == "user" else "Assistant"
        lines.append(f"{role}: {text}")
    return "\n".join(lines)


def contextualize(message: str, history: list[dict] | None) -> str:
    """Return a standalone version of `message`, or `message` unchanged when there
    is no usable history or anything goes wrong."""
    transcript = _format_history(history or [])
    if not transcript:
        return message
    try:
        resp = _client().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content":
                    f"Conversation so far:\n{transcript}\n\nLatest message: {message}\n\n"
                    "Standalone question:"},
            ],
            temperature=0.0,
            reasoning_effort="low",
            reasoning_format="parsed",
            max_completion_tokens=256,
        )
        out = (resp.choices[0].message.content or "").strip().strip('"').strip()
    except Exception:
        return message
    # Guard against an empty or implausibly long rewrite.
    if not out or len(out) > MAX_REWRITE_CHARS:
        return message
    return out