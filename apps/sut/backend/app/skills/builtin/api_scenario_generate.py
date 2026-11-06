"""Skill: generate a multi-step API scenario with data flow."""

from __future__ import annotations

import json

from ... import api_models as models
from ...llm_client import chat_json
from ..registry import Skill, SkillError, register
from .api_support import endpoint_text
from .llm_support import require_db, resolve_model

PROMPT_VERSION = "api-scenario-v1"

SYSTEM_PROMPT = """你是接口自动化工程师。把给定的几个接口串成一条可执行的业务场景。

只输出 JSON：
{
  "title": "场景标题",
  "steps": [
    {
      "name": "步骤名",
      "method": "GET|POST|PUT|PATCH|DELETE",
      "url": "接口 path，可用 {{变量}}",
      "headers": {"Content-Type": "application/json"},
      "params": {},
      "body": {},
      "extract": {"变量名": "响应 JSON 路径，如 data.id"},
      "expect": {"status": 200}
    }
  ],
  "expected": "整条链路验证了什么，一句话"
}

硬性要求：
1. 步骤必须按调用顺序排列，前一步的产出用 extract 存成变量，后一步用 {{变量名}} 引用，形成数据流转。
2. 只能使用列表里给出的接口和它们的 path，不要编造。
3. expect.status 写具体数字；创建类接口写 200 或 201，删除类写 200 或 204。
4. body 用真实可用的数据；引用了变量的地方直接写 "{{变量名}}"。
5. 输出 3 到 6 步，覆盖「准备数据 → 主流程 → 校验结果」。
"""


def _normalise(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise SkillError("模型没有返回有效场景", 502)
    title = str(raw.get("title") or "").strip() or "未命名场景"
    steps = raw.get("steps")
    if not isinstance(steps, list) or not steps:
        raise SkillError("模型没有返回有效场景", 502)
    safe: list[dict] = []
    for index, step in enumerate(steps[:8], start=1):
        if not isinstance(step, dict):
            continue
        safe.append(
            {
                "name": str(step.get("name") or f"步骤 {index}")[:120],
                "method": str(step.get("method") or "GET").upper(),
                "url": str(step.get("url") or ""),
                "headers": step.get("headers") if isinstance(step.get("headers"), dict) else {},
                "params": step.get("params") if isinstance(step.get("params"), dict) else {},
                "body": step.get("body"),
                "extract": step.get("extract") if isinstance(step.get("extract"), dict) else {},
                "expect": step.get("expect") if isinstance(step.get("expect"), dict) else {},
            }
        )
    if not safe:
        raise SkillError("模型没有返回有效场景", 502)
    return {
        "title": title[:200],
        "steps": safe,
        "expected": str(raw.get("expected") or "")[:1000],
    }


def _run(payload: dict, ctx: dict) -> dict:
    db = require_db(ctx)
    project_id = payload.get("project_id")
    endpoint_ids = payload.get("endpoint_ids") or []
    if not project_id or not endpoint_ids:
        raise SkillError("缺少 project_id 或 endpoint_ids", 400)

    endpoints = [
        db.get(models.ApiEndpoint, int(item))
        for item in endpoint_ids[:12]
    ]
    endpoints = [item for item in endpoints if item is not None]
    if not endpoints:
        raise SkillError("给出的接口都不存在", 404)

    config = resolve_model(db, payload.get("model_id"))
    blocks = [endpoint_text(item) for item in endpoints]
    user = ["可用接口：", "\n\n".join(blocks)]
    goal = str(payload.get("goal") or "").strip()
    if goal:
        user.append(f"\n业务目标：{goal}")
    user.append("\n请输出一条串联这些接口的场景。")

    raw = chat_json(
        db,
        config,
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(user)},
        ],
        purpose="api_scenario_generation",
        prompt_version=PROMPT_VERSION,
        timeout=120.0,
        max_tokens=6000,
    )
    scenario = _normalise(raw)
    case = models.ApiCase(
        project_id=int(project_id),
        endpoint_id=None,
        kind="scenario",
        title=scenario["title"],
        module=endpoints[0].module,
        steps_json=json.dumps(scenario["steps"], ensure_ascii=False),
        expected=scenario["expected"],
        status="draft",
        source="ai",
        prompt_version=PROMPT_VERSION,
    )
    db.add(case)
    db.commit()
    return {
        "id": case.id,
        "title": case.title,
        "kind": case.kind,
        "module": case.module,
        "steps": scenario["steps"],
        "expected": case.expected,
        "status": case.status,
        "source": case.source,
        "endpoint_ids": [item.id for item in endpoints],
        "model_name": config.model_name,
        "prompt_version": PROMPT_VERSION,
    }


register(
    Skill(
        id="api.scenario.generate",
        name="接口场景生成",
        category="api",
        description="把多个接口串成一条带数据流转的可执行场景，前一步产出作为后一步入参。",
        input_schema={
            "type": "object",
            "properties": {
                "project_id": {"type": "integer"},
                "endpoint_ids": {"type": "array", "items": {"type": "integer"}},
                "goal": {"type": "string"},
                "model_id": {"type": "integer"},
            },
            "required": ["project_id", "endpoint_ids"],
        },
        output_schema={"type": "object", "properties": {"steps": {"type": "array"}}},
        handler=_run,
    )
)
