"""Builtin skill: add a plain-text document to a knowledge base and chunk it."""

from __future__ import annotations

from ..registry import Skill, SkillError, register
from ... import knowledge_models as models
from ...knowledge_chunker import chunk_text


def _run(payload, ctx):
    db = ctx.get("db")
    if db is None:
        raise SkillError("db session missing")
    kb_id = payload.get("kb_id")
    text = str(payload.get("text") or "").strip()
    if not kb_id:
        raise SkillError("kb_id 不能为空")
    if not text:
        raise SkillError("text 不能为空")
    kb = db.get(models.KnowledgeBase, int(kb_id))
    if not kb:
        raise SkillError("知识库不存在", 404)
    pieces = chunk_text(text, kb.chunk_size, kb.chunk_overlap)
    if not pieces:
        raise SkillError("分块结果为空，请检查文本内容")
    document = models.KnowledgeDocument(
        kb_id=kb.id,
        filename=str(payload.get("filename") or "pasted.txt"),
        content_type="text/plain",
        size=len(text.encode("utf-8")),
        char_count=len(text),
        chunk_count=len(pieces),
        source="skill",
    )
    db.add(document)
    db.flush()
    for index, piece in enumerate(pieces):
        db.add(
            models.KnowledgeChunk(
                kb_id=kb.id,
                document_id=document.id,
                seq=index,
                text=piece,
                char_count=len(piece),
            )
        )
    db.commit()
    db.refresh(document)
    return {
        "document": {
            "id": document.id,
            "kb_id": document.kb_id,
            "filename": document.filename,
            "chunk_count": document.chunk_count,
            "char_count": document.char_count,
        }
    }


SKILL = register(
    Skill(
        id="kb.document.add",
        name="知识库写入文档",
        category="knowledge",
        description="把一段纯文本写进知识库并自动分块，返回文档 id 与分块数。",
        input_schema={
            "type": "object",
            "properties": {
                "kb_id": {"type": "integer"},
                "filename": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["kb_id", "text"],
        },
        output_schema={"type": "object"},
        handler=_run,
    )
)
