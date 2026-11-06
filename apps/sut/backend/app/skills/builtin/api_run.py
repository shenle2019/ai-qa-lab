"""Skill: run an API case or scenario."""

from __future__ import annotations

from ... import api_models as models
from ...api_executor import execute_case
from ...api_runner import RunError
from ..registry import Skill, SkillError, register
from .llm_support import require_db


def _run(payload: dict, ctx: dict) -> dict:
    db = require_db(ctx)
    case_id = payload.get("case_id")
    if not case_id:
        raise SkillError("缺少 case_id", 400)
    case = db.get(models.ApiCase, int(case_id))
    if case is None:
        raise SkillError("用例不存在", 404)
    try:
        return execute_case(db, case, base_url=payload.get("base_url"))
    except RunError as exc:
        raise SkillError(str(exc), 400) from exc


register(
    Skill(
        id="api.run",
        name="接口用例执行",
        category="api",
        description="按步骤执行单接口用例或接口场景，变量在步骤间流转，结果落执行记录。",
        input_schema={
            "type": "object",
            "properties": {
                "case_id": {"type": "integer"},
                "base_url": {"type": "string"},
            },
            "required": ["case_id"],
        },
        output_schema={"type": "object", "properties": {"status": {"type": "string"}}},
        handler=_run,
    )
)
