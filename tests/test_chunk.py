"""
Regression check for the paragraph-aware chunker (no network, no keys).

Guards the bug where the overlap paragraph was carried into the next chunk even
when it no longer fit, so the oversize chunk was cut at fixed character offsets,
producing mid-sentence fragments and near-duplicate chunks.

Run:  PYTHONPATH=. python tests/test_chunk.py
"""
from __future__ import annotations

import glob
import os
import sys

from app.ingestion.chunk import chunk_text

MAX = 900


def check(name: str, ok: bool) -> bool:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    return ok


def main() -> int:
    ok = True

    # Two ~480-char sections: the carried overlap plus the next block exceeds
    # the budget, which used to trigger a character-offset split.
    para = "Sentence one is here. " * 21  # ~462 chars
    text = "\n\n".join([
        "# Doc", f"## A\n{para.strip()}", f"## B\n{para.strip()}", f"## C\n{para.strip()}",
    ])
    chunks = chunk_text(text, max_chars=MAX)
    ok &= check("no chunk exceeds the budget", all(len(c) <= MAX for c in chunks))
    ok &= check("every chunk starts at a heading or paragraph",
                all(c.startswith(("#", "Sentence")) for c in chunks))
    ok &= check("no duplicate chunks", len(chunks) == len(set(chunks)))

    # A single block larger than the budget splits at sentences, keeping its heading.
    long_block = "## Long\n" + " ".join(f"Point number {i} applies here." for i in range(60))
    pieces = chunk_text(long_block, max_chars=MAX)
    ok &= check("oversized block is split", len(pieces) > 1)
    ok &= check("each piece keeps the heading", all(p.startswith("## Long\n") for p in pieces))
    ok &= check("each piece ends on a full sentence", all(p.endswith(".") for p in pieces))
    ok &= check("split pieces fit the budget", all(len(p) <= MAX for p in pieces))

    # The real corpus: nothing oversize, nothing duplicated.
    corpus = os.getenv("CORPUS_DIR", "corpus")
    for path in sorted(glob.glob(os.path.join(corpus, "*.md"))):
        if os.path.basename(path).lower() == "sources.md":
            continue
        cs = chunk_text(open(path, encoding="utf-8").read(), max_chars=MAX)
        good = all(len(c) <= MAX for c in cs) and len(cs) == len(set(cs))
        if not good:
            ok &= check(f"corpus {os.path.basename(path)}", False)
    ok &= check("corpus chunks fit the budget with no duplicates", ok)

    print("\nall passed" if ok else "\nFAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
