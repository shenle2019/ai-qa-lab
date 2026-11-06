"""Builtin skill: list knowledge bases with document and chunk counts."""

from __future__ import annotations

from ..registry import Skill, SkillError, register
from ... import knowledge_models as models


def _run(payload, ctx):
    db = ctx.get("db")
    if db is None:
        raise SkillError("db session missing")
    query = db.query(models.KnowledgeBase)
    project_id = payload.get("project_id")
    if project_id is not None:
        query = query.filter(models.KnowledgeBase.project_id == project_id)
    items = query.order_by(models.KnowledgeBase.id.desc()).all()
    result = []
    for item in items:
        documents = (
            db.query(models.KnowledgeDocument)
            .filter(models.KnowledgeDocument.kb_id == item.id)
            .count()
        )
        chunks = db.query(models.KnowledgeChunk).filter(models.KnowledgeChunk.kb_id == item.id).count()
        result.append(
            {
                "id": item.id,
                "name": item.name,
                "project_id": item.project_id,
                "description": item.description,
                "chunk_size": item.chunk_size,
                "chunk_overlap": item.chunk_overlap,
                "document_count": documents,
                "chunk_count": chunks,
            }
        )
    return {"total": len(result), "knowledge_bases": result}


SKILL = register(
    Skill(
        id="kb.list",
        name="知识库列表",
        category="knowledge",
        description="列出知识库及其文档数、分块数。",
        input_schema={"type": "object", "properties": {"project_id": {"type": "integer"}}},
        output_schema={"type": "object"},
        handler=_run,
    )
)
