"""Lexical retrieval over knowledge chunks.

Vector search is a Phase 5 item (it needs the embedding model tab in 系统 AI 配置).
Until then retrieval is token overlap: CJK bigrams + ascii words, with a bonus
when the whole query appears verbatim. That is enough to test whether a document
was chunked well, and the interface stays the same once embeddings arrive.
"""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from . import knowledge_models as models
from .knowledge_chunker import snippet

WORD_PATTERN = re.compile(r"[a-zA-Z0-9_]+")
CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> set[str]:
    lowered = (text or "").lower()
    tokens = set(WORD_PATTERN.findall(lowered))
    for chunk in CJK_PATTERN.findall(lowered):
        if len(chunk) == 1:
            tokens.add(chunk)
            continue
        tokens.update(chunk[index : index + 2] for index in range(len(chunk) - 1))
    return tokens


def search(db: Session, kb_id: int, question: str, top_k: int = 5) -> list[dict]:
    query_tokens = tokenize(question)
    phrase = (question or "").strip()
    rows = (
        db.query(models.KnowledgeChunk, models.KnowledgeDocument.filename)
        .join(models.KnowledgeDocument, models.KnowledgeDocument.id == models.KnowledgeChunk.document_id)
        .filter(models.KnowledgeChunk.kb_id == kb_id)
        .all()
    )
    hits: list[dict] = []
    for chunk, filename in rows:
        overlap = len(query_tokens & tokenize(chunk.text))
        if not overlap and not (phrase and phrase in chunk.text):
            continue
        bonus = 5.0 if phrase and phrase in chunk.text else 0.0
        raw = overlap + bonus
        hits.append(
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "filename": filename,
                "seq": chunk.seq,
                "score": round(raw / max(1, len(query_tokens)), 4),
                "raw_score": raw,
                "snippet": snippet(chunk.text),
                "text": chunk.text,
            }
        )
    hits.sort(key=lambda item: item["raw_score"], reverse=True)
    for hit in hits:
        hit.pop("raw_score", None)
    limit = max(1, min(20, top_k))
    return hits[:limit]
