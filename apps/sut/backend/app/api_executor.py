"""Execute API cases/scenarios and record the result."""

from __future__ import annotations

import json
from typing import Any

from . import api_models as models
from .api_runner import RunError, run_step
from .llm_client import chat_text

DIAGNOSE_PROMPT_VERSION = "api-diagnose-v1"

DIAGNOSE_SYSTEM = """你是接口排障专家。根据一次失败的接口调用（请求、响应、断言），判断最可能的根因。

回答要求：
1. 先给一句结论：问题出在哪一层（请求构造 / 鉴权 / 数据准备 / 服务端 / 断言写错）。
2. 再给 2 到 4 条依据，必须引用请求或响应里的具体字段和值。
3. 最后给一条可执行的修复建议。
4. 用中文，不要超过 200 字，不要罗列无关的可能性。
"""


def asset_base_url(db, endpoint: models.ApiEndpoint | None) -> str | None:
    if endpoint is None or not endpoint.asset_id:
        return None
    asset = db.get(models.ApiAsset, endpoint.asset_id)
    if asset is not None and asset.base_url:
        return asset.base_url
    return None


def resolve_base_url(db, endpoint: models.ApiEndpoint | None) -> str | None:
    return asset_base_url(db, endpoint)


def project_base_url(db, project_id: int) -> str | None:
    """Fallback for scenarios that are not bound to one endpoint."""
    asset = (
        db.query(models.ApiAsset)
        .filter(models.ApiAsset.project_id == project_id)
        .order_by(models.ApiAsset.id.desc())
        .first()
    )
    return asset.base_url if asset is not None else None


def _load_steps(case: models.ApiCase) -> list[dict[str, Any]]:
    try:
        steps = json.loads(case.steps_json or "[]")
    except json.JSONDecodeError:
        steps = []
    if not isinstance(steps, list) or not steps:
        raise RunError("这条用例没有可执行的步骤")
    return steps


def execute_case(
    db,
    case: models.ApiCase,
    *,
    base_url: str | None = None,
    title_prefix: str = "",
) -> dict[str, Any]:
    """Run every step of a case, stop at the first failure, persist an ApiRun."""
    steps = _load_steps(case)
    endpoints = db.get(models.ApiEndpoint, case.endpoint_id) if case.endpoint_id else None
    effective_base = (
        base_url
        or resolve_base_url(db, endpoints)
        or project_base_url(db, case.project_id)
    )

    context: dict[str, Any] = {}
    results: list[dict[str, Any]] = []
    failed = False
    error_text = ""

    for step in steps:
        try:
            outcome = run_step(step, context, effective_base)
        except RunError as exc:
            outcome = {
                "name": str(step.get("name") or "步骤"),
                "ok": False,
                "reason": str(exc),
                "status_code": None,
                "duration_ms": 0,
                "request": {"method": step.get("method"), "url": step.get("url")},
                "response": None,
                "extracted": {},
                "error": str(exc),
            }
        results.append(outcome)
        if not outcome.get("ok"):
            failed = True
            error_text = outcome.get("reason") or outcome.get("error") or "步骤失败"
            break

    first = results[0] if results else {}
    last = results[-1] if results else {}
    run = models.ApiRun(
        project_id=case.project_id,
        case_id=case.id,
        endpoint_id=case.endpoint_id,
        kind=case.kind,
        title=f"{title_prefix}{case.title}"[:200],
        status="failed" if failed else "passed",
        status_code=last.get("status_code"),
        duration_ms=sum(int(item.get("duration_ms") or 0) for item in results),
        request_json=json.dumps(last.get("request") or first.get("request") or {}, ensure_ascii=False)[
            :60000
        ],
        response_json=json.dumps(last.get("response") or {}, ensure_ascii=False)[:60000],
        steps_json=json.dumps(results, ensure_ascii=False)[:120000],
        error=error_text or None,
    )
    db.add(run)
    db.commit()
    return serialise_run(run, steps=results)


def debug_endpoint(
    db,
    endpoint: models.ApiEndpoint,
    *,
    method: str,
    base_url: str | None,
    headers: dict[str, str],
    params: dict[str, Any],
    body: Any,
    expect_status: int | None = None,
) -> dict[str, Any]:
    """Fire one ad-hoc request and record it as a run."""
    step = {
        "name": f"调试 {method.upper()} {endpoint.path}",
        "method": method,
        "url": endpoint.path,
        "headers": headers,
        "params": params,
        "body": body,
        "expect": {"status": expect_status} if expect_status else {},
    }
    effective_base = (
        base_url
        or asset_base_url(db, endpoint)
        or project_base_url(db, endpoint.project_id)
    )
    outcome = run_step(step, {}, effective_base)
    run = models.ApiRun(
        project_id=endpoint.project_id,
        case_id=None,
        endpoint_id=endpoint.id,
        kind="debug",
        title=f"调试 {method.upper()} {endpoint.path}"[:200],
        status="passed" if outcome.get("ok") else "failed",
        status_code=outcome.get("status_code"),
        duration_ms=int(outcome.get("duration_ms") or 0),
        request_json=json.dumps(outcome.get("request") or {}, ensure_ascii=False)[:60000],
        response_json=json.dumps(outcome.get("response") or {}, ensure_ascii=False)[:60000],
        error=outcome.get("reason") or outcome.get("error") or None,
    )
    db.add(run)
    db.commit()
    return serialise_run(run, steps=[outcome])


def serialise_run(run: models.ApiRun, steps: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    try:
        request = json.loads(run.request_json or "{}")
    except json.JSONDecodeError:
        request = {}
    try:
        response = json.loads(run.response_json or "{}")
    except json.JSONDecodeError:
        response = {}
    if steps is None:
        try:
            steps = json.loads(run.steps_json or "[]")
        except json.JSONDecodeError:
            steps = []
    variables: dict[str, Any] = {}
    for item in steps or []:
        for key, value in (item.get("extracted") or {}).items():
            variables[key] = value
    return {
        "id": run.id,
        "project_id": run.project_id,
        "case_id": run.case_id,
        "endpoint_id": run.endpoint_id,
        "kind": run.kind,
        "title": run.title,
        "status": run.status,
        "status_code": run.status_code,
        "duration_ms": run.duration_ms,
        "request": request,
        "response": response,
        "error": run.error,
        "ai_root_cause": run.ai_root_cause,
        "created_at": run.created_at,
        "steps": steps or [],
        "variables": variables,
    }


def diagnose(db, run: models.ApiRun, config, *, force: bool = False) -> str:
    """Ask the model what went wrong; cache the answer on the run row."""
    if run.ai_root_cause and not force:
        return run.ai_root_cause
    try:
        request = json.loads(run.request_json or "{}")
    except json.JSONDecodeError:
        request = {}
    try:
        response = json.loads(run.response_json or "{}")
    except json.JSONDecodeError:
        response = {}

    payload = {
        "title": run.title,
        "status": run.status,
        "error": run.error,
        "request": request,
        "response": response,
    }
    text = chat_text(
        db,
        config,
        [
            {"role": "system", "content": DIAGNOSE_SYSTEM},
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False)[:12000],
            },
        ],
        purpose="api_diagnose",
        prompt_version=DIAGNOSE_PROMPT_VERSION,
        timeout=90.0,
        max_tokens=1200,
        temperature=0.2,
    )
    run.ai_root_cause = text.strip()
    db.commit()
    return run.ai_root_cause
