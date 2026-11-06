"""Builtin skill: edit a test case in place."""

from __future__ import annotations

from ..registry import Skill, SkillError, register
from ... import platform_models as models

EDITABLE = ("title", "module", "priority", "steps", "expected")
PRIORITIES = {"low", "medium", "high"}


def _serialize(case):
    return {
        "id": case.id,
        "project_id": case.project_id,
        "title": case.title,
        "module": case.module,
        "priority": case.priority,
        "steps": case.steps,
        "expected": case.expected,
        "status": case.status,
        "source": case.source,
    }


def _run(payload, ctx):
    db = ctx.get("db")
    if db is None:
        raise SkillError("db session missing")
    case_id = payload.get("case_id")
    if case_id is None:
        raise SkillError("case_id 不能为空")
    case = db.get(models.TestCase, int(case_id))
    if case is None:
        raise SkillError("case not found", status_code=404)

    changed = []
    for field in EDITABLE:
        if field not in payload or payload[field] is None:
            continue
        value = str(payload[field])
        if field == "title" and not value.strip():
            raise SkillError("标题不能为空")
        if field == "priority" and value not in PRIORITIES:
            raise SkillError(f"priority 只能是 {sorted(PRIORITIES)}")
        setattr(case, field, value.strip() if field == "title" else value)
        changed.append(field)

    if not changed:
        raise SkillError("没有需要修改的字段")

    db.commit()
    db.refresh(case)
    return {"case": _serialize(case), "changed": changed}


SKILL = register(
    Skill(
        id="case.update",
        name="编辑用例",
        category="case",
        description="修改用例的标题、模块、优先级、步骤或预期结果。",
        input_schema={
            "type": "object",
            "required": ["case_id"],
            "properties": {
                "case_id": {"type": "integer"},
                "title": {"type": "string"},
                "module": {"type": "string"},
                "priority": {"type": "string", "enum": sorted(PRIORITIES)},
                "steps": {"type": "string"},
                "expected": {"type": "string"},
            },
        },
        output_schema={"type": "object"},
        handler=_run,
    )
)
