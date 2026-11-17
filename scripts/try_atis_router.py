"""
Robustness test of the semantic router against the ATIS intent dataset.

ATIS is a public benchmark of airline-travel utterances (flight search, airfares,
ground transport, ...). None of its intents is one this system supports, so it is
an independent, out-of-distribution test: the router should NOT send these to the
transactional pipeline (which would ask the passenger for a booking reference).
Acceptable routes are out_of_scope or informational (where the hallucination gate
falls back safely).

It draws a fixed-seed, intent-stratified sample from the ATIS test split, runs
each utterance through the real router (app.router.classify, including the margin
safeguard), and reports the route distribution overall and per ATIS intent. Full
results are written to a CSV for the thesis.

Usage (repo root, venv active, .env with GEMINI_API_KEY):
    python -m scripts.try_atis_router --file data/atis/atis_intents_test.csv
    python -m scripts.try_atis_router --file ... --n 200 --out atis_router_results.csv

Each utterance costs one Gemini embedding call; --delay paces them to stay inside
the free-tier rate limit.
"""
from __future__ import annotations

import argparse
import collections
import csv
import random
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.router import classify


def load(path: str) -> list[tuple[str, str]]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if "," not in line:
                continue
            label, text = line.split(",", 1)
            label, text = label.strip(), text.strip()
            if label and text:
                rows.append((label, text))
    return rows


def stratified_sample(rows, n, seed):
    """Sample n rows keeping each intent's share, with at least one per intent."""
    rng = random.Random(seed)
    by_intent = collections.defaultdict(list)
    for label, text in rows:
        by_intent[label].append(text)
    total = len(rows)
    sample = []
    for label, texts in sorted(by_intent.items()):
        k = max(1, round(n * len(texts) / total))
        for text in rng.sample(texts, min(k, len(texts))):
            sample.append((label, text))
    rng.shuffle(sample)
    return sample


def classify_with_retry(text, attempts=4):
    for i in range(attempts):
        try:
            return classify(text)
        except Exception as e:  # rate limit or transient error: back off and retry
            if i == attempts - 1:
                raise
            wait = 5 * (i + 1)
            print(f"    (retry in {wait}s: {type(e).__name__})")
            time.sleep(wait)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="path to atis_intents_test.csv")
    ap.add_argument("--n", type=int, default=200, help="sample size (default 200)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--delay", type=float, default=0.7, help="seconds between calls")
    ap.add_argument("--out", default="atis_router_results.csv")
    args = ap.parse_args()

    rows = load(args.file)
    sample = stratified_sample(rows, args.n, args.seed)
    print(f"Loaded {len(rows)} utterances; testing a stratified sample of {len(sample)} (seed {args.seed}).\n")

    results = []
    for i, (intent, text) in enumerate(sample, 1):
        r = classify_with_retry(text)
        results.append({
            "atis_intent": intent, "text": text, "route": r["route"],
            "score": round(float(r.get("score", 0)), 3),
            "biased": r.get("biased", ""),
        })
        if i % 25 == 0:
            print(f"  {i}/{len(sample)} done")
        time.sleep(args.delay)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    n = len(results)
    overall = collections.Counter(r["route"] for r in results)
    print("\nRoute distribution (all sampled utterances)")
    for route, c in overall.most_common():
        print(f"  {route:15} {c:4}  {100 * c / n:5.1f}%")

    wrong = overall.get("transactional", 0)
    print(f"\nSent to the transactional pipeline (would be asked for a PNR): "
          f"{wrong}/{n} = {100 * wrong / n:.1f}%")
    biased = sum(1 for r in results if r["biased"] is True)
    if biased:
        print(f"Margin safeguard fired on {biased}/{n} utterances.")

    print("\nBy ATIS intent (route counts)")
    per = collections.defaultdict(collections.Counter)
    for r in results:
        per[r["atis_intent"]][r["route"]] += 1
    for intent, c in sorted(per.items(), key=lambda kv: -sum(kv[1].values())):
        parts = ", ".join(f"{k} {v}" for k, v in c.most_common())
        print(f"  {intent:22} {sum(c.values()):4}   {parts}")

    tx = [r for r in results if r["route"] == "transactional"]
    if tx:
        print("\nExamples routed to transactional")
        for r in tx[:15]:
            print(f"  [{r['atis_intent']}] {r['text']}")

    print(f"\nFull results written to {args.out}")


if __name__ == "__main__":
    main()