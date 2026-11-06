"""Builtin skill: list platform projects."""

from __future__ import annotations

from ..registry import Skill, SkillError, register
from ... import platform_models as models


def _run(payload, ctx):
    db = ctx.get("db")
    if db is None:
        raise SkillError("db session missing")
    rows = db.query(models.Project).order_by(models.Project.id.desc()).limit(200).all()
    return {
        "total": len(rows),
        "projects": [
            {"id": r.id, "name": r.name, "description": r.description} for r in rows
        ],
    }


SKILL = register(
    Skill(
        id="project.list",
        name="项目列表",
        category="project",
        description="列出平台里的全部项目。",
        input_schema={"type": "object", "properties": {}},
        output_schema={"type": "object"},
        handler=_run,
    )
)
