"""
Regression check for the semantic router's class boundaries.

Runs each message through the real router (app.router.classify, margin
safeguard on) and checks the route. Prints all three class scores per query so
drift is visible before it flips a route.

Two groups:
  boundary     - the original boundary queries; the first three are near-copies
                 of exemplars, so these mainly guard the exemplar set itself.
  paraphrases  - reworded queries that must NOT be exemplars; these test that
                 the router generalises across each boundary.

Needs GEMINI_API_KEY (one embedding call per query, plus the exemplars on first
use). Exits 1 if any query routes wrongly.

Run:  PYTHONPATH=. python tests/test_router_boundary.py
"""
from __future__ import annotations

import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.router import EXAMPLES, classify

BOUNDARY = [
    ("What’s the status of my flight?", "transactional"),
    ("What time does my flight leave?", "transactional"),
    ("What documents do I need for my flight?", "informational"),
    ("Can I change my flight date?", "informational"),
]

PARAPHRASES = [
    ("Is my flight on time?", "transactional"),
    ("Has my flight been delayed?", "transactional"),
    ("Can you check my flight for me?", "transactional"),
    ("I’d like to move to a window seat", "transactional"),
    ("Can I move my flight to Friday?", "informational"),
    ("What do I need to bring for my flight to London?", "informational"),
    ("How early should I be at the airport for my flight?", "informational"),
    # Arranging a service is informational, even though "book"/"get" also
    # appear in flight-search wording.
    ("Where can I get the unaccompanied minor service?", "informational"),
    ("How do I sign my child up to travel alone?", "informational"),
    ("Who do I contact to get help at the airport for my mother?", "informational"),
    ("Is there a flight from Nairobi to Mombasa tomorrow?", "out_of_scope"),
    ("How much is a ticket to Dubai?", "out_of_scope"),
]


def _norm(text: str) -> str:
    return text.replace("’", "'").strip().lower()


def check_paraphrases_not_exemplars() -> list[str]:
    """Paraphrases only test generalisation if they aren't in the exemplar set."""
    exemplars = {_norm(t) for texts in EXAMPLES.values() for t in texts}
    return [msg for msg, _ in PARAPHRASES if _norm(msg) in exemplars]


def classify_with_retry(text: str, attempts: int = 4) -> dict:
    for i in range(attempts):
        try:
            return classify(text)
        except Exception as e:  # rate limit or transient error: back off and retry
            if i == attempts - 1:
                raise
            wait = 5 * (i + 1)
            print(f"    (retry in {wait}s: {type(e).__name__})")
            time.sleep(wait)


def run_group(name: str, cases: list[tuple[str, str]]) -> int:
    print(f"\n{name}")
    print(f"  {'':4}  {'route (want -> got)':32}  {'trans':>6}  {'info':>6}  {'oos':>6}  message")
    failures = 0
    for msg, want in cases:
        r = classify_with_retry(msg)
        s = r["scores"]
        ok = r["route"] == want
        failures += not ok
        flags = []
        if r["biased"]:
            flags.append("biased")
        if r["topic"]:
            flags.append(f"topic={r['topic']}")
        route = f"{want} -> {r['route']}"
        print(
            f"  {'PASS' if ok else 'FAIL'}  {route:32}  "
            f"{s['transactional']:6.3f}  {s['informational']:6.3f}  {s['out_of_scope']:6.3f}  "
            f"{msg}" + (f"  [{', '.join(flags)}]" if flags else "")
        )
    return failures


def main() -> int:
    leaked = check_paraphrases_not_exemplars()
    if leaked:
        print("FAIL: these paraphrases are also exemplars, so they don't test generalisation:")
        for msg in leaked:
            print(f"  - {msg}")
        return 1

    failures = run_group("Boundary queries", BOUNDARY)
    failures += run_group("Paraphrases (not exemplars)", PARAPHRASES)

    total = len(BOUNDARY) + len(PARAPHRASES)
    print(f"\n{total - failures}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
