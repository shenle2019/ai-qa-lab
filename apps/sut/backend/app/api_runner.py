"""HTTP execution for API cases and scenarios."""

from __future__ import annotations

import json
import re
import time
from typing import Any

import httpx

VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.\[\]-]+)\s*\}\}")
DEFAULT_TIMEOUT = 20.0
MAX_BODY_CHARS = 20000


class RunError(ValueError):
    """Raised when a step cannot be executed as written."""


def render(value: Any, ctx: dict[str, Any], strict: bool = False) -> Any:
    """Recursively substitute ``{{name}}`` / ``{{a.b}}`` placeholders.

    ``strict`` turns a missing variable into a readable RunError instead of
    silently producing an empty string (which used to surface as a confusing
    307 redirect from ``/api/projects/``).
    """

    if isinstance(value, str):
        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            found = lookup(ctx, key)
            if found is None:
                if strict:
                    raise RunError(f"变量 {{{{{key}}}}} 没有解析到值，请检查上一步的 extract")
                return ""
            return str(found)

        return VAR_PATTERN.sub(repl, value)
    if isinstance(value, list):
        return [render(item, ctx, strict) for item in value]
    if isinstance(value, dict):
        return {key: render(item, ctx, strict) for key, item in value.items()}
    return value


def lookup(ctx: dict[str, Any], path: str) -> Any:
    current: Any = ctx
    for part in [p for p in path.split(".") if p]:
        if isinstance(current, dict):
            if part in current:
                current = current[part]
                continue
            # tolerate numeric dict keys such as {"200": ...}
            if part.isdigit() and int(part) in current:
                current = current[int(part)]
                continue
            return None
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
            continue
        return None
    return current


def extract(payload: Any, expr: str, headers: dict[str, str] | None = None) -> Any:
    """Pull a value out of a response.

    Supported expressions: ``$.a.b``, ``a.b``, ``a.0.b``, ``header:Location``.
    """
    expr = (expr or "").strip()
    if not expr:
        return None
    if expr.lower().startswith("header:"):
        name = expr.split(":", 1)[1].strip()
        headers = headers or {}
        for key, value in headers.items():
            if key.lower() == name.lower():
                return value
        return None
    path = expr[2:] if expr.startswith("$.") else expr.lstrip("$").lstrip(".")
    return lookup(payload if isinstance(payload, dict) else {"_": payload}, path)


def _absolute(url: str, base_url: str | None) -> str:
    raw = (url or "").strip()
    if not raw:
        raise RunError("接口地址为空")
    if raw.lower().startswith(("http://", "https://")):
        return raw
    if not base_url:
        raise RunError("接口是相对路径，且没有配置 Base URL")
    return f"{base_url.rstrip('/')}/{raw.lstrip('/')}"


def _parse_body(raw: Any) -> tuple[Any, bool]:
    """Return (payload, is_json)."""
    if raw in (None, "", {}):
        return None, False
    if isinstance(raw, (dict, list)):
        return raw, True
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None, False
        try:
            return json.loads(text), True
        except json.JSONDecodeError:
            return text, False
    return raw, False


def send(
    method: str,
    url: str,
    *,
    base_url: str | None = None,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    body: Any = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Perform one HTTP request and normalise the result."""
    target = _absolute(url, base_url)
    payload, is_json = _parse_body(body)
    started = time.perf_counter()
    try:
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            response = client.request(
                method.upper(),
                target,
                headers=headers or None,
                params=params or None,
                json=payload if is_json else None,
                content=None if is_json else (payload if isinstance(payload, str) else None),
            )
    except httpx.HTTPError as exc:
        return {
            "ok": False,
            "status_code": None,
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "request": {"method": method.upper(), "url": target, "headers": headers or {}, "params": params or {}, "body": payload},
            "response": None,
            "error": f"{type(exc).__name__}: {exc}",
        }

    duration = int((time.perf_counter() - started) * 1000)
    text = response.text
    try:
        parsed: Any = response.json()
    except (json.JSONDecodeError, ValueError):
        parsed = None
    return {
        "ok": True,
        "status_code": response.status_code,
        "duration_ms": duration,
        "request": {"method": method.upper(), "url": target, "headers": headers or {}, "params": params or {}, "body": payload},
        "response": {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": text[:MAX_BODY_CHARS],
            "json": parsed,
        },
        "error": None,
    }


def check_expectation(result: dict[str, Any], expect: dict[str, Any] | None) -> tuple[bool, str]:
    """Compare a result against ``{status, contains, json_path, equals}``."""
    if not expect:
        if not result.get("ok"):
            return False, result.get("error") or "请求失败"
        return True, ""
    if not result.get("ok"):
        return False, result.get("error") or "请求失败"

    status = expect.get("status")
    if status not in (None, "", []):
        wanted = status if isinstance(status, list) else [status]
        codes = {int(item) for item in wanted if str(item).strip().lstrip("0").isdigit() or str(item).isdigit()}
        if codes and result.get("status_code") not in codes:
            return False, f"状态码期望 {'/'.join(str(c) for c in sorted(codes))}，实际 {result.get('status_code')}"

    contains = expect.get("contains")
    if contains:
        response = result.get("response") or {}
        if str(contains) not in str(response.get("body") or ""):
            return False, f"响应里没有找到「{contains}」"

    path = expect.get("json_path")
    if path:
        response = result.get("response") or {}
        actual = extract(response.get("json"), str(path), response.get("headers"))
        wanted = expect.get("equals")
        if wanted is not None and str(actual) != str(wanted):
            return False, f"{path} 期望 {wanted}，实际 {actual}"
        if wanted is None and actual is None:
            return False, f"响应里取不到 {path}"
    return True, ""


def run_step(step: dict[str, Any], ctx: dict[str, Any], base_url: str | None) -> dict[str, Any]:
    """Render and execute one step, then merge extracted variables into ``ctx``."""
    if not isinstance(step, dict):
        raise RunError("步骤格式不对")
    method = str(step.get("method") or "GET")
    url = render(step.get("url") or step.get("path") or "", ctx, strict=True)
    headers = render(step.get("headers") or {}, ctx, strict=True)
    params = render(step.get("params") or {}, ctx, strict=True)
    body = render(step.get("body"), ctx, strict=True)
    result = send(
        method,
        str(url),
        base_url=render(step.get("base_url") or base_url or "", ctx, strict=True) or None,
        headers={str(k): str(v) for k, v in (headers or {}).items()},
        params={str(k): v for k, v in (params or {}).items()},
        body=body,
    )
    extracted: dict[str, Any] = {}
    for name, expr in (step.get("extract") or {}).items():
        response = result.get("response") or {}
        value = extract(response.get("json"), str(expr), response.get("headers"))
        extracted[str(name)] = value
        ctx[str(name)] = value
    ok, reason = check_expectation(result, step.get("expect"))
    return {
        "name": str(step.get("name") or step.get("title") or f"{method} {url}"),
        "ok": ok,
        "reason": reason,
        "status_code": result.get("status_code"),
        "duration_ms": result.get("duration_ms"),
        "request": result.get("request"),
        "response": result.get("response"),
        "extracted": extracted,
        "error": result.get("error"),
    }
