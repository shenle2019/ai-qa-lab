"""Generate structured test cases from a requirement using the configured model."""

from __future__ import annotations

import json
import re

from sqlalchemy.orm import Session

from . import llm_client, llm_models

PROMPT_VERSION = "case-gen-v1"
MODULES = {"api", "web", "app", "perf"}
PRIORITIES = {"low", "medium", "high"}
METHOD_PATTERN = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\b", re.IGNORECASE)
PATH_PATTERN = re.compile(r"/[A-Za-z0-9_\-./{}]*")
STATUS_PATTERN = re.compile(r"\b(\d{3})\b")
EMPTY_DATA = {"", "无", "无请求体", "none", "null", "-"}


def _normalize_step(raw) -> dict | None:
    if isinstance(raw, str):
        raw = {"action": raw}
    if not isinstance(raw, dict):
        return None
    action = str(raw.get("action", ""))
    target = str(raw.get("target", ""))
    method_match = METHOD_PATTERN.search(f"{action} {target}")
    if not method_match:
        return None
    path_match = PATH_PATTERN.search(target) or PATH_PATTERN.search(f"{action} {target}")
    if not path_match:
        return None
    status_match = STATUS_PATTERN.search(str(raw.get("assert", "")))
    if not status_match:
        return None
    data = str(raw.get("data", "")).strip()
    if data.lower() in EMPTY_DATA:
        data = ""
    return {
        "action": method_match.group(1).upper(),
        "target": path_match.group(0),
        "data": data[:2000],
        "assert": f"status={status_match.group(1)}",
    }

SYSTEM_PROMPT = """你是测试开发工程师。把需求转成可直接执行的接口测试用例。
只输出 JSON，不要输出 Markdown、不要输出解释。格式：
{"cases":[{"title":"用例标题","module":"api","priority":"low|medium|high","steps":[{"action":"GET|POST|PUT|PATCH|DELETE","target":"/相对路径","data":"JSON字符串或空字符串","assert":"status=200"}],"expected":"整体预期"}]}

硬性规则：
1. action 只能是 GET、POST、PUT、PATCH、DELETE 之一，不能写中文。
2. target 必须以 / 开头的相对路径，不能写完整 URL。
3. data 是请求体 JSON 字符串；没有请求体时写空字符串。
4. assert 只能是 "status=三位状态码"，不要写自然语言。
5. 不要生成“解析响应体”“检查功能正常”这类非 HTTP 步骤；一条用例只保留 1-3 个真实请求步骤。
6. 覆盖正常路径、异常路径和边界值；标题唯一且不超过 60 字。

示例：
{"cases":[{"title":"工单列表返回 200","module":"api","priority":"high","steps":[{"action":"GET","target":"/api/tickets","data":"","assert":"status=200"}],"expected":"返回工单数组"}]}
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
            normalized_step = _normalize_step(step)
            if normalized_step is not None:
                clean_steps.append(normalized_step)
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
