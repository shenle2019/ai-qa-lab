"""Builtin skill: turn a requirement (plus its analysis) into a test plan."""

from __future__ import annotations

import json

from ..registry import Skill, SkillError, register
from ... import llm_client, platform_models, requirement_models
from .llm_support import require_db, resolve_model

PROMPT_VERSION = "req-plan-v1"

SYSTEM_PROMPT = """你是测试负责人。基于需求材料与分析结果，产出一份可以直接排期的测试计划。

只输出一个 JSON 对象，不要输出解释文字，结构如下：
{
  "goal": "本次测试要达成的目标，一两句话",
  "scope_in": ["本次覆盖的范围"],
  "scope_out": ["本次明确不覆盖的范围"],
  "approach": "测试策略：分层方式、主要手段、优先顺序",
  "person_days": 3.5,
  "milestones": [
    {"name": "阶段名称", "days": 1, "deliverable": "该阶段交付物"}
  ],
  "environments": ["需要的测试环境或账号"],
  "test_data": ["需要准备的测试数据"],
  "risks": ["可能导致延期或漏测的风险"]
}

要求：
1. person_days 为数字，等于 milestones 的 days 之和，保留一位小数。
2. 范围要具体到功能点，不要写「核心功能」这类空话。
3. 全部使用简体中文。
"""


def _num(value, default=0.0) -> float:
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return default


def _normalise(raw: dict) -> dict:
    def as_list(value):
        return value if isinstance(value, list) else []

    milestones = []
    for item in as_list(raw.get("milestones")):
        if not isinstance(item, dict):
            continue
        milestones.append(
            {
                "name": str(item.get("name") or "").strip(),
                "days": _num(item.get("days"), 0.5),
                "deliverable": str(item.get("deliverable") or "").strip(),
            }
        )

    total = _num(sum(m["days"] for m in milestones), 0.0)
    person_days = _num(raw.get("person_days"), total)
    if total and abs(person_days - total) > 0.05:
        person_days = total

    return {
        "goal": str(raw.get("goal") or "").strip(),
        "scope_in": [str(v).strip() for v in as_list(raw.get("scope_in")) if str(v).strip()],
        "scope_out": [str(v).strip() for v in as_list(raw.get("scope_out")) if str(v).strip()],
        "approach": str(raw.get("approach") or "").strip(),
        "person_days": person_days,
        "milestones": [m for m in milestones if m["name"]],
        "environments": [str(v).strip() for v in as_list(raw.get("environments")) if str(v).strip()],
        "test_data": [str(v).strip() for v in as_list(raw.get("test_data")) if str(v).strip()],
        "risks": [str(v).strip() for v in as_list(raw.get("risks")) if str(v).strip()],
    }


def _run(payload, ctx):
    db = require_db(ctx)
    requirement_id = payload.get("requirement_id")
    if not requirement_id:
        raise SkillError("requirement_id 不能为空")
    req = db.get(requirement_models.Requirement, int(requirement_id))
    if req is None:
        raise SkillError("requirement not found", status_code=404)

    analysis = {}
    if req.analysis_json:
        try:
            analysis = json.loads(req.analysis_json)
        except json.JSONDecodeError:
            analysis = {}
    if not analysis.get("features"):
        raise SkillError("请先完成需求分析，再生成测试计划", status_code=409)

    context = json.dumps(
        {
            "title": req.title,
            "body": req.body[:6000],
            "analysis": analysis,
        },
        ensure_ascii=False,
    )
    config = resolve_model(db, payload.get("model_id"))
    try:
        raw = llm_client.chat_json(
            db,
            config,
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            purpose="requirement_plan",
            prompt_version=PROMPT_VERSION,
            timeout=90.0,
            max_tokens=4000,
        )
    except llm_client.LLMError as exc:
        raise SkillError(str(exc), status_code=502) from exc

    plan = _normalise(raw)
    req.plan_json = json.dumps(plan, ensure_ascii=False)
    req.status = "planned"

    created_plan = None
    if payload.get("create_plan", True):
        existing = (
            db.query(platform_models.TestPlan)
            .filter(
                platform_models.TestPlan.project_id == req.project_id,
                platform_models.TestPlan.name == f"{req.title} · 测试计划",
            )
            .first()
        )
        plan_row = existing or platform_models.TestPlan(
            project_id=req.project_id,
            name=f"{req.title} · 测试计划",
            status="draft",
        )
        if existing is None:
            db.add(plan_row)
            db.flush()
        created_plan = {"id": plan_row.id, "name": plan_row.name}
    db.commit()

    return {
        "requirement_id": req.id,
        "model_name": config.model_name,
        "prompt_version": PROMPT_VERSION,
        "plan": plan,
        "test_plan": created_plan,
    }


SKILL = register(
    Skill(
        id="requirement.plan",
        name="生成测试计划",
        category="requirement",
        description="基于需求与分析结果生成测试计划：目标、覆盖范围、策略、人天与里程碑。",
        input_schema={
            "type": "object",
            "required": ["requirement_id"],
            "properties": {
                "requirement_id": {"type": "integer"},
                "model_id": {"type": "integer"},
                "create_plan": {"type": "boolean", "default": True},
            },
        },
        output_schema={"type": "object"},
        handler=_run,
    )
)
