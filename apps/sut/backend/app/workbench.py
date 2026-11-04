import ipaddress
import json
import socket
import time
from typing import Any, Literal
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import settings

router = APIRouter(prefix="/api/workbench", tags=["workbench"])

MAX_BODY_PREVIEW = 200_000
METADATA_HOSTS = {"169.254.169.254", "metadata.google.internal", "metadata"}
SPECIAL_USE = {"0.0.0.0", "::"}


def _forbidden_ip(ip: ipaddress._BaseAddress) -> bool:
    if str(ip) in SPECIAL_USE:
        return True
    if ip.is_multicast or ip.is_unspecified:
        return True
    if settings.is_production():
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_site_local
        )
    return False


def _validate_target(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="url must start with http:// or https://")
    host = (parsed.hostname or "").lower()
    if not host:
        raise HTTPException(status_code=400, detail="url host is missing")
    if host in METADATA_HOSTS:
        raise HTTPException(status_code=400, detail="metadata address is blocked")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise HTTPException(status_code=400, detail="url host cannot be resolved") from exc
    for info in infos:
        address = info[4][0].split("%", 1)[0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid resolved address") from exc
        if str(ip) in METADATA_HOSTS or _forbidden_ip(ip):
            raise HTTPException(status_code=400, detail="target address is blocked")


class Assertion(BaseModel):
    type: Literal["status", "max_ms", "body_contains", "json_path_exists", "json_path_equals"]
    path: str | None = None
    expected: Any = None


class WorkbenchRequest(BaseModel):
    name: str = "request"
    method: str = "GET"
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    body: str | None = None
    timeout_ms: int = Field(default=10000, ge=100, le=10000)
    assertions: list[Assertion] = Field(default_factory=list)


class WorkbenchResult(BaseModel):
    name: str
    passed: bool
    status: int | None
    elapsed_ms: int
    size: int
    failures: list[str]
    body_preview: str


class RunPayload(BaseModel):
    requests: list[WorkbenchRequest] = Field(min_length=1, max_length=10)


def _json_path(data: Any, path: str) -> Any:
    normalized = path.strip()
    if normalized.startswith("$"):
        normalized = normalized[1:]
    if normalized.startswith("."):
        normalized = normalized[1:]
    if not normalized:
        return data

    current = data
    for part in normalized.replace("[", ".[").split("."):
        if not part:
            continue
        if part.startswith("[") and part.endswith("]"):
            current = current[int(part[1:-1])]
        else:
            current = current[part]
    return current


def _check_assertion(assertion: Assertion, result: dict[str, Any], text: str) -> str | None:
    if assertion.type == "status":
        expected = int(assertion.expected)
        if result["status"] != expected:
            return f"status expected {expected}, got {result['status']}"
        return None

    if assertion.type == "max_ms":
        limit = int(assertion.expected)
        if result["elapsed_ms"] > limit:
            return f"elapsed {result['elapsed_ms']}ms exceeds {limit}ms"
        return None

    if assertion.type == "body_contains":
        if str(assertion.expected) not in text:
            return f"body does not contain {assertion.expected!r}"
        return None

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return f"response is not JSON for {assertion.type}"

    try:
        value = _json_path(payload, assertion.path or "$")
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        return f"json path {assertion.path!r} not found: {exc}"

    if assertion.type == "json_path_exists":
        if value is None:
            return f"json path {assertion.path!r} is null"
        return None

    if value != assertion.expected:
        return f"json path {assertion.path!r} expected {assertion.expected!r}, got {value!r}"
    return None


async def _execute(request: WorkbenchRequest) -> WorkbenchResult:
    _validate_target(request.url)

    started = time.perf_counter()
    try:
        timeout = request.timeout_ms / 1000
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            response = await client.request(
                request.method.upper(),
                request.url,
                headers=request.headers,
                content=request.body.encode("utf-8") if request.body else None,
            )
    except httpx.HTTPError as exc:
        elapsed = int((time.perf_counter() - started) * 1000)
        return WorkbenchResult(
            name=request.name,
            passed=False,
            status=None,
            elapsed_ms=elapsed,
            size=0,
            failures=[f"request failed: {exc}"],
            body_preview="",
        )

    elapsed = int((time.perf_counter() - started) * 1000)
    text = response.text
    result_meta = {"status": response.status_code, "elapsed_ms": elapsed}
    failures = []
    for assertion in request.assertions:
        failure = _check_assertion(assertion, result_meta, text)
        if failure:
            failures.append(failure)

    return WorkbenchResult(
        name=request.name,
        passed=not failures,
        status=response.status_code,
        elapsed_ms=elapsed,
        size=len(response.content),
        failures=failures,
        body_preview=text[:MAX_BODY_PREVIEW],
    )


@router.post("/send", response_model=WorkbenchResult)
async def send(request: WorkbenchRequest) -> WorkbenchResult:
    return await _execute(request)


@router.post("/run", response_model=list[WorkbenchResult])
async def run(payload: RunPayload) -> list[WorkbenchResult]:
    results = []
    for request in payload.requests:
        results.append(await _execute(request))
    return results
