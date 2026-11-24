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


SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


def _split_block(block: str, max_chars: int) -> list[str]:
    """Split one block that exceeds the budget at sentence boundaries. If it
    starts with a header line, the header is repeated on every piece so each
    keeps its section context. A single sentence longer than the budget (rare)
    is cut at character offsets as a last resort."""
    header = ""
    body = block
    first, _, rest = block.partition("\n")
    if HEADER_RE.match(first) and rest:
        header, body = first + "\n", rest
    room = max_chars - len(header)

    pieces: list[str] = []
    cur = ""
    for sent in SENTENCE_END_RE.split(body):
        while len(sent) > room:  # one oversized sentence
            if cur:
                pieces.append(cur)
                cur = ""
            pieces.append(sent[:room])
            sent = sent[room:]
        if cur and len(cur) + 1 + len(sent) > room:
            pieces.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}" if cur else sent
    if cur:
        pieces.append(cur)
    return [header + p for p in pieces]


def chunk_text(text: str, max_chars: int = 900, overlap_blocks: int = 1) -> list[str]:
    blocks: list[str] = []
    for b in _blocks(text):
        blocks.extend(_split_block(b, max_chars) if len(b) > max_chars else [b])

    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0

    def joined_len(parts: list[str]) -> int:
        return sum(len(x) for x in parts) + 2 * max(0, len(parts) - 1)

    for b in blocks:
        if cur and cur_len + 2 + len(b) > max_chars:
            chunks.append("\n\n".join(cur))
            # Carry the overlap only while the next block still fits beside it;
            # otherwise the chunk would exceed the budget. (Previously it was
            # carried regardless, and the oversize chunk was then cut at fixed
            # character offsets, producing mid-sentence fragments and duplicates.)
            carry = cur[-overlap_blocks:] if overlap_blocks else []
            while carry and joined_len(carry + [b]) > max_chars:
                carry = carry[1:]
            cur = list(carry)
            cur_len = joined_len(cur)
        cur_len += len(b) + (2 if cur else 0)
        cur.append(b)

    if cur:
        chunks.append("\n\n".join(cur))
    return chunks
