"""Generate structured test cases from a requirement using the configured model."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from . import llm_client, llm_models

PROMPT_VERSION = "case-gen-v1"
MODULES = {"api", "web", "app", "perf"}
PRIORITIES = {"low", "medium", "high"}

SYSTEM_PROMPT = """你是测试开发工程师。把需求转成可执行的结构化测试用例。
只输出 JSON，不要输出 Markdown。格式：
{"cases":[{"title":"用例标题","module":"api|web|app|perf","priority":"low|medium|high","steps":[{"action":"操作","target":"对象","data":"数据","assert":"断言"}],"expected":"整体预期"}]}
要求：
1. 覆盖正常路径、异常路径和边界值。
2. 每条用例只验证一个明确的预期。
3. 步骤必须可执行，不要写“检查功能正常”这类空话。
4. 标题唯一，不超过 60 字。
"""


def _normalize(raw: dict, limit: int) -> list[dict]:
    items = raw.get("cases")
    if not isinstance(items, list):
        raise llm_client.LLMError("模型返回缺少 cases 数组")

    normalized: list[dict] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()[:200]
        if not title or title in seen:
            continue
        seen.add(title)
        module = str(item.get("module", "api")).lower()
        priority = str(item.get("priority", "medium")).lower()
        steps = item.get("steps") or []
        if isinstance(steps, str):
            steps = [{"action": "执行", "target": steps, "data": "", "assert": ""}]
        clean_steps = []
        for step in steps[:30]:
            if isinstance(step, str):
                clean_steps.append({"action": step, "target": "", "data": "", "assert": ""})
            elif isinstance(step, dict):
                clean_steps.append(
                    {
                        "action": str(step.get("action", ""))[:200],
                        "target": str(step.get("target", ""))[:200],
                        "data": str(step.get("data", ""))[:500],
                        "assert": str(step.get("assert", ""))[:500],
                    }
                )
        if not clean_steps:
            continue
        normalized.append(
            {
                "title": title,
                "module": module if module in MODULES else "api",
                "priority": priority if priority in PRIORITIES else "medium",
                "steps": clean_steps,
                "expected": str(item.get("expected", ""))[:1000],
            }
        )
        if len(normalized) >= limit:
            break
    if not normalized:
        raise llm_client.LLMError("模型没有返回有效用例")
    return normalized


def generate(
    db: Session,
    config: llm_models.ModelConfig,
    requirement: str,
    limit: int,
) -> list[dict]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"最多生成 {limit} 条用例。需求如下：\n{requirement}",
        },
    ]
    raw = llm_client.chat_json(
        db,
        config,
        messages,
        purpose="case_generation",
        prompt_version=PROMPT_VERSION,
        timeout=90.0,
        max_tokens=6000,
    )
    return _normalize(raw, limit)


def steps_to_text(steps: list[dict]) -> str:
    lines = []
    for index, step in enumerate(steps, start=1):
        parts = [step.get("action", ""), step.get("target", "")]
        text = " ".join(part for part in parts if part).strip()
        if step.get("data"):
            text += f"（数据：{step['data']}）"
        if step.get("assert"):
            text += f" 断言：{step['assert']}"
        lines.append(f"{index}. {text}")
    return "\n".join(lines)


def steps_to_json(steps: list[dict]) -> str:
    return json.dumps(steps, ensure_ascii=False)
