"""Execute approved API cases against a target base URL.

Cases store an executable step list in `steps_json`:
    [{"action": "GET", "target": "/api/tickets", "data": "", "assert": "status=200"}]

Only relative targets are allowed so a case cannot be used to reach arbitrary
hosts. Non-API modules are reported as skipped until dedicated runners exist.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from . import platform_models as models

METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
MAX_STEPS = 30
MAX_CASES = 50
DEFAULT_TIMEOUT = 15.0
STATUS_PATTERN = re.compile(r"status\s*[=: ]\s*(\d{3})", re.IGNORECASE)


def default_base_url() -> str:
    explicit = os.getenv("EXEC_BASE_URL")
    if explicit:
        return explicit
    port = os.getenv("PORT", "8000")
    return f"http://127.0.0.1:{port}"


def _expected_status(text: str) -> int | None:
    if not text:
        return None
    match = STATUS_PATTERN.search(text)
    if match:
        return int(match.group(1))
    stripped = text.strip()
    if stripped.isdigit() and len(stripped) == 3:
        return int(stripped)
    return None


def execute_case(case: models.TestCase, base_url: str, timeout: float = DEFAULT_TIMEOUT) -> dict:
    started = time.perf_counter()

    def fail(message: str) -> dict:
        return {
            "status": "failed",
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "message": message[:2000],
        }

    try:
        steps = json.loads(case.steps_json or "[]")
    except json.JSONDecodeError:
        return fail("steps_json 不是合法 JSON")
    if not isinstance(steps, list) or not steps:
        return fail("没有可执行步骤")

    for index, step in enumerate(steps[:MAX_STEPS], start=1):
        if not isinstance(step, dict):
            return fail(f"第 {index} 步不是对象")
        method = str(step.get("action", "")).upper()
        if method not in METHODS:
            return fail(f"第 {index} 步 action 不是 HTTP 方法: {method or '空'}")
        target = str(step.get("target", "")).strip()
        if not target.startswith("/"):
            return fail(f"第 {index} 步 target 必须是相对路径: {target or '空'}")

        data = step.get("data", "")
        body = None
        if isinstance(data, (dict, list)):
            body = data
        elif isinstance(data, str) and data.strip():
            try:
                body = json.loads(data)
            except json.JSONDecodeError:
                body = data

        try:
            response = httpx.request(
                method,
                base_url.rstrip("/") + target,
                json=body,
                timeout=timeout,
            )
        except Exception as exc:  # noqa: BLE001 - report transport errors as case failures
            return fail(f"第 {index} 步请求失败: {exc}")

        expected = _expected_status(str(step.get("assert", "")))
        if expected is not None and response.status_code != expected:
            return fail(
                f"第 {index} 步期望 {expected}，实际 {response.status_code}: {response.text[:200]}"
            )

    return {
        "status": "passed",
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "message": f"{len(steps)} 步全部通过",
    }


def execute_plan(
    db: Session,
    plan: models.TestPlan,
    cases: list[models.TestCase],
    base_url: str | None = None,
) -> models.TestExecution:
    target = (base_url or default_base_url()).rstrip("/")
    execution = models.TestExecution(plan_id=plan.id, status="running", started_at=datetime.utcnow())
    db.add(execution)
    db.flush()

    passed = failed = skipped = total_ms = 0
    started = time.perf_counter()
    for case in cases[:MAX_CASES]:
        if case.module != "api":
            result = {
                "status": "skipped",
                "duration_ms": 0,
                "message": f"暂不支持 module={case.module} 的自动执行",
            }
        else:
            result = execute_case(case, target)
        if result["status"] == "passed":
            passed += 1
        elif result["status"] == "failed":
            failed += 1
        else:
            skipped += 1
        total_ms += result["duration_ms"]
        db.add(
            models.TestResult(
                execution_id=execution.id,
                case_id=case.id,
                case_name=case.title,
                status=result["status"],
                duration_ms=result["duration_ms"],
                message=result["message"],
            )
        )

    execution.total = passed + failed + skipped
    execution.passed = passed
    execution.failed = failed
    execution.skipped = skipped
    execution.duration_ms = int((time.perf_counter() - started) * 1000)
    execution.status = "failed" if failed else ("skipped" if skipped and not passed else "passed")
    plan.status = execution.status
    db.commit()
    db.refresh(execution)
    return execution
