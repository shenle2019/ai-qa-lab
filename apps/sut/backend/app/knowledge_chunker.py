"""Split documents into retrievable chunks.

The strategy stays deliberately simple so the result is predictable:
paragraphs first, then greedy packing into windows of ``chunk_size`` characters
with ``chunk_overlap`` characters of overlap. Chunks remember their index so a
retrieval hit can be traced back to a position inside the source document.
"""

from __future__ import annotations

import re

PARAGRAPH_SPLIT = re.compile(r"\n\s*\n+")


def _normalise(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def split_paragraphs(text: str) -> list[str]:
    blocks = [block.strip() for block in PARAGRAPH_SPLIT.split(_normalise(text))]
    return [block for block in blocks if block]


def chunk_text(text: str, chunk_size: int = 600, chunk_overlap: int = 100) -> list[str]:
    """Return chunks of roughly ``chunk_size`` characters."""
    if chunk_size < 50:
        chunk_size = 50
    if chunk_overlap < 0:
        chunk_overlap = 0
    if chunk_overlap >= chunk_size:
        chunk_overlap = max(0, chunk_size // 5)

    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return []

    chunks: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if buffer:
                chunks.append(buffer.strip())
                buffer = ""
            for start in range(0, len(paragraph), chunk_size - chunk_overlap):
                piece = paragraph[start : start + chunk_size].strip()
                if piece:
                    chunks.append(piece)
            continue
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= chunk_size:
            buffer = candidate
            continue
        chunks.append(buffer.strip())
        tail = buffer[-chunk_overlap:] if chunk_overlap else ""
        buffer = f"{tail}\n\n{paragraph}".strip() if tail else paragraph
        while len(buffer) > chunk_size:
            chunks.append(buffer[:chunk_size].strip())
            buffer = buffer[chunk_size - chunk_overlap :].strip()
    if buffer.strip():
        chunks.append(buffer.strip())
    return [chunk for chunk in chunks if chunk]


def snippet(text: str, limit: int = 200) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + "…"
