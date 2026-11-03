"""
Paragraph-aware chunking for the policy corpus.

The corpus documents use blank lines between paragraphs, so the chunker splits
on paragraph boundaries first and packs whole paragraphs into chunks up to a
character budget. A markdown header line is merged into the paragraph that
follows it (so a heading never becomes a lone chunk and stays as context for its
section), and consecutive chunks share one paragraph of overlap so a point that
spans a boundary is still retrievable from either side.
"""
from __future__ import annotations

import re

HEADER_RE = re.compile(r"^#{1,6}\s")


def _blocks(text: str) -> list[str]:
    text = text.replace("\r\n", "\n")
    raw = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    merged: list[str] = []
    i = 0
    while i < len(raw):
        if HEADER_RE.match(raw[i]) and i + 1 < len(raw):
            merged.append(raw[i] + "\n" + raw[i + 1])
            i += 2
        else:
            merged.append(raw[i])
            i += 1
    return merged


def chunk_text(text: str, max_chars: int = 900, overlap_blocks: int = 1) -> list[str]:
    blocks = _blocks(text)
    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0

    def flush():
        if cur:
            chunks.append("\n\n".join(cur))

    for b in blocks:
        add = len(b) + (2 if cur else 0)
        if cur and cur_len + add > max_chars:
            flush()
            carry = cur[-overlap_blocks:] if overlap_blocks and len(cur[-1]) < max_chars else []
            cur = list(carry)
            cur_len = sum(len(x) for x in cur) + 2 * max(0, len(cur) - 1)
            add = len(b) + (2 if cur else 0)
        cur.append(b)
        cur_len += add

    flush()

    # Hard-split any single block that is itself larger than the budget.
    final: list[str] = []
    for c in chunks:
        if len(c) <= max_chars:
            final.append(c)
        else:
            step = max_chars - 120
            s = 0
            while s < len(c):
                final.append(c[s:s + max_chars])
                s += step
    return final
