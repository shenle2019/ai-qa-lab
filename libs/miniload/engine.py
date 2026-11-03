"""Threaded load engine: constant VUs, ramp-up, thresholds, percentiles."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import requests


@dataclass
class Scenario:
    name: str
    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    json_body: Any = None
    data: str | None = None
    timeout: float = 10.0
    think_time: float = 0.0


@dataclass
class LoadResult:
    scenario: Scenario
    vus: int
    duration: float
    ramp_up: float
    elapsed: float
    total: int
    success: int
    errors: int
    error_rate: float
    rps: float
    percentiles: dict[str, float]
    status_counts: dict[str, int]
    error_messages: dict[str, int]
    thresholds: dict[str, float | None]
    violations: list[str]
    passed: bool
    started_at: str
    latencies_ms: list[float] = field(default_factory=list)


def _percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * ratio))
    return round(ordered[index], 2)


def _worker(
    scenario: Scenario,
    index: int,
    vus: int,
    start_at: float,
    end_at: float,
    ramp_up: float,
) -> tuple[list[float], int, int, dict[str, int], dict[str, int]]:
    session = requests.Session()
    latencies: list[float] = []
    success = 0
    errors = 0
    status_counts: dict[str, int] = {}
    error_messages: dict[str, int] = {}

    delay = ramp_up * (index / vus) if vus else 0.0
    target = start_at + delay
    now = time.perf_counter()
    if target > now:
        time.sleep(target - now)

    while time.perf_counter() < end_at:
        began = time.perf_counter()
        try:
            response = session.request(
                scenario.method,
                scenario.url,
                headers=scenario.headers or None,
                json=scenario.json_body,
                data=scenario.data,
                timeout=scenario.timeout,
            )
            elapsed_ms = (time.perf_counter() - began) * 1000
            latencies.append(elapsed_ms)
            status_counts[str(response.status_code)] = status_counts.get(str(response.status_code), 0) + 1
            if 200 <= response.status_code < 400:
                success += 1
            else:
                errors += 1
                key = f"HTTP {response.status_code}"
                error_messages[key] = error_messages.get(key, 0) + 1
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - began) * 1000
            latencies.append(elapsed_ms)
            errors += 1
            key = f"{type(exc).__name__}: {exc}"[:200]
            error_messages[key] = error_messages.get(key, 0) + 1
        finally:
            if scenario.think_time:
                time.sleep(scenario.think_time)

    return latencies, success, errors, status_counts, error_messages


def run_load(
    scenario: Scenario,
    *,
    vus: int = 10,
    duration: float = 5.0,
    ramp_up: float = 0.0,
    p95_ms: float | None = None,
    error_rate: float | None = None,
    min_rps: float | None = None,
) -> LoadResult:
    if vus < 1:
        raise ValueError("vus must be >= 1")
    if duration <= 0:
        raise ValueError("duration must be > 0")

    started_at = datetime.now().isoformat(timespec="seconds")
    start_at = time.perf_counter() + 0.05
    end_at = start_at + ramp_up + duration

    with ThreadPoolExecutor(max_workers=vus) as pool:
        futures = [
            pool.submit(_worker, scenario, index, vus, start_at, end_at, ramp_up)
            for index in range(vus)
        ]
        results = [future.result() for future in futures]

    latencies: list[float] = []
    success = 0
    errors = 0
    status_counts: dict[str, int] = {}
    error_messages: dict[str, int] = {}
    for worker_latencies, worker_success, worker_errors, worker_status, worker_messages in results:
        latencies.extend(worker_latencies)
        success += worker_success
        errors += worker_errors
        for key, value in worker_status.items():
            status_counts[key] = status_counts.get(key, 0) + value
        for key, value in worker_messages.items():
            error_messages[key] = error_messages.get(key, 0) + value

    total = success + errors
    elapsed = max(time.perf_counter() - start_at, 0.001)
    error_rate_value = (errors / total) if total else 0.0
    rps = total / elapsed
    percentiles = {
        "min": round(min(latencies), 2) if latencies else 0.0,
        "p50": _percentile(latencies, 0.50),
        "p90": _percentile(latencies, 0.90),
        "p95": _percentile(latencies, 0.95),
        "p99": _percentile(latencies, 0.99),
        "max": round(max(latencies), 2) if latencies else 0.0,
        "avg": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
    }

    thresholds = {"p95_ms": p95_ms, "error_rate": error_rate, "min_rps": min_rps}
    violations: list[str] = []
    if p95_ms is not None and percentiles["p95"] > p95_ms:
        violations.append(f"p95 {percentiles['p95']}ms > {p95_ms}ms")
    if error_rate is not None and error_rate_value > error_rate:
        violations.append(f"error_rate {error_rate_value:.2%} > {error_rate:.2%}")
    if min_rps is not None and rps < min_rps:
        violations.append(f"rps {rps:.1f} < {min_rps}")

    return LoadResult(
        scenario=scenario,
        vus=vus,
        duration=duration,
        ramp_up=ramp_up,
        elapsed=round(elapsed, 3),
        total=total,
        success=success,
        errors=errors,
        error_rate=error_rate_value,
        rps=round(rps, 2),
        percentiles=percentiles,
        status_counts=status_counts,
        error_messages=error_messages,
        thresholds=thresholds,
        violations=violations,
        passed=not violations,
        started_at=started_at,
        latencies_ms=latencies,
    )
