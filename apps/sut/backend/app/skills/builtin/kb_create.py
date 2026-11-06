"""Builtin skill: create a knowledge base."""

from __future__ import annotations

from ..registry import Skill, SkillError, register
from ... import knowledge_models as models


def _run(payload, ctx):
    db = ctx.get("db")
    if db is None:
        raise SkillError("db session missing")
    name = str(payload.get("name") or "").strip()
    if not name:
        raise SkillError("知识库名称不能为空")
    project_id = payload.get("project_id")
    existing = (
        db.query(models.KnowledgeBase)
        .filter(models.KnowledgeBase.name == name)
        .filter(models.KnowledgeBase.project_id == project_id)
        .first()
    )
    if existing:
        raise SkillError("同名知识库已存在", 409)
    item = models.KnowledgeBase(
        project_id=project_id,
        name=name,
        description=str(payload.get("description") or ""),
        chunk_size=int(payload.get("chunk_size") or 600),
        chunk_overlap=int(payload.get("chunk_overlap") or 100),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "kb": {
            "id": item.id,
            "name": item.name,
            "project_id": item.project_id,
            "chunk_size": item.chunk_size,
            "chunk_overlap": item.chunk_overlap,
        }
    }


SKILL = register(
    Skill(
        id="kb.create",
        name="创建知识库",
        category="knowledge",
        description="新建一个知识库，指定分块大小与重叠字符数。",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "project_id": {"type": "integer"},
                "chunk_size": {"type": "integer", "default": 600},
                "chunk_overlap": {"type": "integer", "default": 100},
            },
            "required": ["name"],
        },
        output_schema={"type": "object"},
        handler=_run,
    )
)
