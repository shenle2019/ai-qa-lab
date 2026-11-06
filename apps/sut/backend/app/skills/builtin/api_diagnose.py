"""Skill: AI root-cause for a failed API run."""

from __future__ import annotations

from ... import api_models as models
from ...api_executor import diagnose
from ..registry import Skill, SkillError, register
from .llm_support import require_db, resolve_model


def _run(payload: dict, ctx: dict) -> dict:
    db = require_db(ctx)
    run_id = payload.get("run_id")
    if not run_id:
        raise SkillError("缺少 run_id", 400)
    run = db.get(models.ApiRun, int(run_id))
    if run is None:
        raise SkillError("执行记录不存在", 404)
    if run.status == "passed":
        raise SkillError("这条记录是成功的，不需要归因", 400)
    config = resolve_model(db, payload.get("model_id"))
    text = diagnose(db, run, config, force=bool(payload.get("force")))
    return {
        "run_id": run.id,
        "status": run.status,
        "ai_root_cause": text,
        "model_name": config.model_name,
    }


register(
    Skill(
        id="api.diagnose",
        name="失败归因",
        category="api",
        description="对失败的接口执行记录做根因分析，给出结论、依据和修复建议。",
        input_schema={
            "type": "object",
            "properties": {
                "run_id": {"type": "integer"},
                "model_id": {"type": "integer"},
                "force": {"type": "boolean"},
            },
            "required": ["run_id"],
        },
        output_schema={"type": "object", "properties": {"ai_root_cause": {"type": "string"}}},
        handler=_run,
    )
)
