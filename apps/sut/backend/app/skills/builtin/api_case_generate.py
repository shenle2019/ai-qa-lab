"""Skill: generate single-interface API cases."""

from __future__ import annotations

import json

from ... import api_models as models
from ...llm_client import chat_json
from ..registry import Skill, SkillError, register
from .api_support import endpoint_text, kb_context
from .llm_support import require_db, resolve_model

PROMPT_VERSION = "api-case-v1"

SYSTEM_PROMPT = """你是接口测试工程师。根据给定的接口定义，产出可以直接执行的接口用例。

只输出 JSON，结构如下：
{
  "cases": [
    {
      "title": "用例标题（中文，说明场景）",
      "module": "所属模块",
      "steps": [
        {
          "name": "步骤名",
          "method": "GET|POST|PUT|PATCH|DELETE",
          "url": "接口路径，必须是给定接口的 path，可以带 {{变量}}",
          "headers": {"Content-Type": "application/json"},
          "params": {"查询参数": "值"},
          "body": {},
          "extract": {"变量名": "响应 JSON 路径，如 data.id"},
          "expect": {"status": 200, "contains": "响应里应出现的文本"}
        }
      ],
      "expected": "这条用例验证什么，一句话"
    }
  ]
}

要求：
1. 用例要覆盖正常流程、边界值、必填缺失、越权/未登录、非法参数这些角度，不要只写成功路径。
2. 每条用例一个步骤即可；`expect.status` 必须写具体数字。
3. `url` 只能使用给定接口的 path，不要自己编造接口。
4. `body` 用真实可用的示例数据，不要写 "string" 这种占位符。
5. 标题要能一眼看出在测什么，不要写成「测试用例1」。
"""


def _normalise(raw: dict, endpoint: models.ApiEndpoint, count: int) -> list[dict]:
    cases = raw.get("cases") if isinstance(raw, dict) else None
    if not isinstance(cases, list):
        raise SkillError("模型没有返回有效用例", 502)
    cleaned: list[dict] = []
    for item in cases[:count]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        steps = item.get("steps")
        if not title or not isinstance(steps, list):
            continue
        safe_steps: list[dict] = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            safe_steps.append(
                {
                    "name": str(step.get("name") or title)[:120],
                    "method": str(step.get("method") or endpoint.method).upper(),
                    "url": str(step.get("url") or endpoint.path),
                    "headers": step.get("headers") if isinstance(step.get("headers"), dict) else {},
                    "params": step.get("params") if isinstance(step.get("params"), dict) else {},
                    "body": step.get("body") if step.get("body") is not None else None,
                    "extract": step.get("extract") if isinstance(step.get("extract"), dict) else {},
                    "expect": step.get("expect") if isinstance(step.get("expect"), dict) else {},
                }
            )
        if not safe_steps:
            continue
        cleaned.append(
            {
                "title": title[:200],
                "module": str(item.get("module") or endpoint.module)[:80],
                "steps": safe_steps,
                "expected": str(item.get("expected") or "")[:1000],
            }
        )
    if not cleaned:
        raise SkillError("模型没有返回有效用例", 502)
    return cleaned


def _run(payload: dict, ctx: dict) -> dict:
    db = require_db(ctx)
    endpoint_id = payload.get("endpoint_id")
    if not endpoint_id:
        raise SkillError("缺少 endpoint_id", 400)
    endpoint = db.get(models.ApiEndpoint, int(endpoint_id))
    if endpoint is None:
        raise SkillError("接口不存在", 404)

    count = max(1, min(15, int(payload.get("count") or 5)))
    config = resolve_model(db, payload.get("model_id"))
    query = f"{endpoint.name} {endpoint.path} {endpoint.module}"
    context = kb_context(db, payload.get("kb_id"), query)

    user = [endpoint_text(endpoint)]
    if context:
        user.append(f"\n【项目资料】\n{context}")
    user.append(f"\n请生成 {count} 条接口用例。")

    raw = chat_json(
        db,
        config,
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(user)},
        ],
        purpose="api_case_generation",
        prompt_version=PROMPT_VERSION,
        timeout=120.0,
        max_tokens=6000,
    )
    cases = _normalise(raw, endpoint, count)
    created = []
    for item in cases:
        case = models.ApiCase(
            project_id=endpoint.project_id,
            endpoint_id=endpoint.id,
            kind="case",
            title=item["title"],
            module=item["module"],
            steps_json=json.dumps(item["steps"], ensure_ascii=False),
            expected=item["expected"],
            status="draft",
            source="ai",
            prompt_version=PROMPT_VERSION,
        )
        db.add(case)
        db.flush()
        created.append(
            {
                "id": case.id,
                "title": case.title,
                "module": case.module,
                "kind": case.kind,
                "steps": item["steps"],
                "expected": case.expected,
                "status": case.status,
                "source": case.source,
            }
        )
    db.commit()
    return {
        "endpoint_id": endpoint.id,
        "endpoint": f"{endpoint.method} {endpoint.path}",
        "cases": created,
        "count": len(created),
        "model_name": config.model_name,
        "prompt_version": PROMPT_VERSION,
        "used_knowledge": bool(context),
    }


register(
    Skill(
        id="api.case.generate",
        name="接口用例生成",
        category="api",
        description="根据接口定义生成可直接执行的接口用例（草稿），覆盖正常、边界与异常路径。",
        input_schema={
            "type": "object",
            "properties": {
                "endpoint_id": {"type": "integer"},
                "count": {"type": "integer", "minimum": 1, "maximum": 15},
                "kb_id": {"type": "integer"},
                "model_id": {"type": "integer"},
            },
            "required": ["endpoint_id"],
        },
        output_schema={"type": "object", "properties": {"cases": {"type": "array"}}},
        handler=_run,
    )
)
