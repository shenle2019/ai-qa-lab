"""Shared helpers for API automation skills."""

from __future__ import annotations

import json
from typing import Any

from ... import api_models as models
from ...knowledge_search import search as kb_search


def endpoint_brief(endpoint: models.ApiEndpoint) -> dict[str, Any]:
    return {
        "id": endpoint.id,
        "method": endpoint.method,
        "path": endpoint.path,
        "name": endpoint.name,
        "module": endpoint.module,
        "params": json.loads(endpoint.params_json or "[]"),
        "body": json.loads(endpoint.body_json or "{}"),
        "responses": json.loads(endpoint.responses_json or "[]"),
    }


def endpoint_text(endpoint: models.ApiEndpoint) -> str:
    brief = endpoint_brief(endpoint)
    lines = [
        f"接口：{brief['method']} {brief['path']}",
        f"名称：{brief['name'] or '（未命名）'}",
        f"模块：{brief['module']}",
    ]
    if endpoint.summary:
        lines.append(f"说明：{endpoint.summary}")
    params = brief["params"]
    if params:
        lines.append("参数：")
        for item in params:
            flag = "必填" if item.get("required") else "可选"
            lines.append(
                f"  - {item.get('name')}（{item.get('in', 'query')}，{item.get('type', 'string')}，{flag}）"
                f"{(item.get('description') or '')}"
            )
    fields = (brief["body"] or {}).get("fields") or []
    if fields:
        lines.append("请求体字段：")
        for item in fields:
            flag = "必填" if item.get("required") else "可选"
            lines.append(
                f"  - {item.get('name')}（{item.get('type', 'string')}，{flag}）{(item.get('description') or '')}"
            )
    responses = brief["responses"]
    if responses:
        lines.append("响应：")
        for item in responses:
            fields = item.get("fields") or []
            head = f"  - {item.get('code')} {item.get('description') or ''}".rstrip()
            lines.append(head)
            for field in fields[:12]:
                flag = "必填" if field.get("required") else "可选"
                lines.append(
                    f"    · {field.get('name')}（{field.get('type', 'string')}，{flag}）"
                    f"{(field.get('description') or '')}"
                )
    return "\n".join(lines)


def kb_context(db, kb_id: int | None, query: str, top_k: int = 3) -> str:
    """Best-effort knowledge snippet; never break generation because of it."""
    if not kb_id:
        return ""
    try:
        result = kb_search(db, kb_id, query, top_k=top_k)
    except Exception:  # noqa: BLE001 - knowledge is optional context
        return ""
    return (result or {}).get("context") or ""


def html_safe(value: Any, limit: int = 1200) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text[:limit]
