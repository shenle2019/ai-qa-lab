"""Builtin skill: list test cases (with optional project filter)."""

from __future__ import annotations

from ..registry import Skill, register
from ... import platform_models as models


def _run(payload, ctx):
    db = ctx.get("db")
    if db is None:
        from ..registry import SkillError

        raise SkillError("db session missing")
    query = db.query(models.TestCase)
    project_id = payload.get("project_id")
    if project_id is not None:
        query = query.filter(models.TestCase.project_id == project_id)
    limit = int(payload.get("limit") or 100)
    limit = max(1, min(limit, 500))
    rows = query.order_by(models.TestCase.id.desc()).limit(limit).all()
    return {
        "total": len(rows),
        "cases": [
            {
                "id": r.id,
                "project_id": r.project_id,
                "title": r.title,
                "module": r.module,
                "priority": r.priority,
                "status": r.status,
                "source": r.source,
            }
            for r in rows
        ],
    }


SKILL = register(
    Skill(
        id="case.list",
        name="用例列表",
        category="case",
        description="按项目查询测试用例，返回 id/标题/模块/优先级/状态。",
        input_schema={
            "type": "object",
            "properties": {
                "project_id": {"type": "integer"},
                "limit": {"type": "integer", "default": 100},
            },
        },
        output_schema={"type": "object"},
        handler=_run,
    )
)
