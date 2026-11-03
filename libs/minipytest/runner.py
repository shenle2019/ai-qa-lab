"""Execution engine: fixtures, retries, skip/xfail, and summaries."""

from __future__ import annotations

import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from .collect import collect
from .errors import AssertionFailure, FixtureError, FixtureNotFound, Skipped
from .fixtures import FixtureManager
from .markers import first_mark, marker_names, parse_marker_expr
from .model import Attempt, Case, CaseResult, Failure, RunResult


FRAMEWORK_DIR = Path(__file__).resolve().parent


def _find_location(tb: Any, rootdir: Path) -> str:
    if tb is None:
        return ""
    frames = list(traceback.walk_tb(tb))
    for frame, lineno in reversed(frames):
        if frame.f_locals.get("__tracebackhide__"):
            continue
        try:
            path = Path(frame.f_code.co_filename).resolve()
            if path == FRAMEWORK_DIR or path.parent == FRAMEWORK_DIR:
                continue
            return f"{path.relative_to(rootdir).as_posix()}:{lineno}"
        except (ValueError, OSError):
            continue
    if frames:
        frame, lineno = frames[-1]
        return f"{frame.f_code.co_filename}:{lineno}"
    return ""


def _failure_from_exception(exc: BaseException, phase: str, rootdir: Path) -> Failure:
    location = _find_location(exc.__traceback__, rootdir)
    if isinstance(exc, AssertionFailure):
        return Failure(
            message=exc.message,
            phase=phase,
            type=exc.__class__.__name__,
            traceback="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            location=exc.location or location,
            expected=exc.expected,
            actual=exc.actual,
            diff=exc.diff,
        )
    return Failure(
        message=str(exc) or exc.__class__.__name__,
        phase=phase,
        type=exc.__class__.__name__,
        traceback="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        location=location,
    )


def _mark_reason(mark_obj: Any) -> str:
    if mark_obj is None:
        return ""
    if mark_obj.args and isinstance(mark_obj.args[0], str):
        return mark_obj.args[0]
    return str(mark_obj.kwargs.get("reason", ""))


def _condition(mark_obj: Any) -> bool:
    if mark_obj is None:
        return False
    if mark_obj.args:
        condition = mark_obj.args[0]
    else:
        condition = mark_obj.kwargs.get("condition", False)
    if callable(condition):
        condition = condition()
    return bool(condition)


def _max_attempts(mark_obj: Any, cli_retry: int) -> int:
    if mark_obj is not None:
        if mark_obj.args:
            value = mark_obj.args[0]
        else:
            value = mark_obj.kwargs.get("attempts", 2)
        return max(1, int(value))
    return max(1, int(cli_retry or 1))


def _run_case(case: Case, manager: FixtureManager, rootdir: Path, cli_retry: int) -> CaseResult:
    manager.begin_case(case, case.path.parent)

    skip_mark = first_mark(case.marks, "skip")
    if skip_mark is not None:
        return CaseResult(
            case=case,
            status="skipped",
            phase="setup",
            duration_ms=0.0,
            skip_reason=_mark_reason(skip_mark),
        )

    skipif_mark = first_mark(case.marks, "skipif")
    if skipif_mark is not None and _condition(skipif_mark):
        return CaseResult(
            case=case,
            status="skipped",
            phase="setup",
            duration_ms=0.0,
            skip_reason=_mark_reason(skipif_mark),
        )

    xfail_mark = first_mark(case.marks, "xfail")
    retry_mark = first_mark(case.marks, "retry")
    max_attempts = _max_attempts(retry_mark, cli_retry)

    attempts: list[Attempt] = []
    teardown_errors: list[Failure] = []
    final_status = "failed"
    final_failure: Failure | None = None
    final_phase = "call"
    skip_reason: str | None = None
    case_start = time.perf_counter()

    for attempt_no in range(1, max_attempts + 1):
        manager.reset_function()
        attempt_start = time.perf_counter()
        status = "passed"
        failure: Failure | None = None
        phase = "call"

        try:
            manager.setup_autouse()
            kwargs = manager.resolve_test_params(case.func, case, drop_self=case.cls is not None)
            if case.cls is not None:
                instance = case.cls()
                case.func(instance, **kwargs)
            else:
                case.func(**kwargs)
        except Skipped as exc:
            status = "skipped"
            phase = "setup"
            failure = None
            skip_reason = exc.reason or str(exc)
        except FixtureNotFound as exc:
            status = "error"
            phase = "setup"
            failure = Failure(
                message=str(exc),
                phase="setup",
                type=exc.__class__.__name__,
                location=f"{case.path.as_posix()}",
            )
        except FixtureError as exc:
            status = "error"
            phase = exc.phase
            failure = _failure_from_exception(exc.original, exc.phase, rootdir)
        except AssertionFailure as exc:
            status = "failed"
            phase = "call"
            failure = _failure_from_exception(exc, "call", rootdir)
        except Exception as exc:
            status = "failed"
            phase = "call"
            failure = _failure_from_exception(exc, "call", rootdir)
        finally:
            function_teardown = manager.finalize_function()
            if function_teardown:
                teardown_errors.extend(function_teardown)
                if status == "passed":
                    status = "error"
                    phase = "teardown"
                    failure = function_teardown[0]

        duration_ms = (time.perf_counter() - attempt_start) * 1000
        attempts.append(Attempt(attempt_no, status, duration_ms, failure))
        final_status, final_failure, final_phase = status, failure, phase

        if status in {"passed", "skipped", "error"}:
            break

    xfail_reason: str | None = None
    if xfail_mark is not None and final_status in {"passed", "failed"}:
        xfail_reason = _mark_reason(xfail_mark)
        if final_status == "failed":
            final_status = "xfailed"
        else:
            strict = bool(xfail_mark.kwargs.get("strict", False))
            if strict:
                final_status = "failed"
                final_failure = Failure(
                    message="strict xfail: test passed unexpectedly",
                    phase="call",
                    type="XPass",
                    location=case.nodeid,
                )
            else:
                final_status = "xpassed"

    return CaseResult(
        case=case,
        status=final_status,
        phase=final_phase,
        duration_ms=(time.perf_counter() - case_start) * 1000,
        attempts=attempts,
        failure=final_failure,
        skip_reason=skip_reason,
        xfail_reason=xfail_reason,
        fixtures=list(manager.case_timings),
        teardown_errors=teardown_errors,
    )


def run(
    paths: Sequence[str | Path],
    *,
    rootdir: Path | str | None = None,
    marker_expr: str | None = None,
    retry: int = 1,
    command: Sequence[str] | None = None,
) -> RunResult:
    rootdir_path = Path(rootdir or Path.cwd()).resolve()
    started_at = datetime.now().isoformat(timespec="seconds")
    started = time.perf_counter()

    collected = collect(paths, rootdir_path)
    selector = parse_marker_expr(marker_expr)
    selected = [case for case in collected.cases if selector(marker_names(case.marks))]
    deselected = len(collected.cases) - len(selected)

    manager = FixtureManager()
    results: list[CaseResult] = []
    for case in selected:
        results.append(_run_case(case, manager, rootdir_path, retry))
    manager.finalize_module()
    manager.finalize_session()

    summary = {
        "total": len(results),
        "passed": 0,
        "failed": 0,
        "error": 0,
        "skipped": 0,
        "xfailed": 0,
        "xpassed": 0,
        "deselected": deselected,
        "retried": 0,
        "flaky": 0,
        "collection_errors": len(collected.errors),
        "finalization_errors": len(manager.run_finalization_errors),
    }
    for result in results:
        if result.status in summary:
            summary[result.status] += 1
        if len(result.attempts) > 1:
            summary["retried"] += 1
        if result.status == "passed" and any(attempt.status == "failed" for attempt in result.attempts):
            summary["flaky"] += 1

    if collected.errors:
        exit_code = 2
    elif summary["failed"] or summary["error"] or summary["finalization_errors"]:
        exit_code = 1
    elif not selected:
        exit_code = 3
    else:
        exit_code = 0

    return RunResult(
        rootdir=rootdir_path,
        command=list(command or sys.argv),
        started_at=started_at,
        duration_ms=(time.perf_counter() - started) * 1000,
        tests=results,
        summary=summary,
        collection_errors=collected.errors,
        finalization_errors=manager.run_finalization_errors,
        deselected=deselected,
        exit_code=exit_code,
    )
