"""Command-line interface for minipytest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .errors import UsageError
from .reporting import TOOL_VERSION, write_html_report, write_json_report
from .runner import run


def _status_label(status: str) -> str:
    return {
        "passed": "PASS",
        "failed": "FAIL",
        "error": "ERROR",
        "skipped": "SKIP",
        "xfailed": "XFAIL",
        "xpassed": "XPASS",
    }.get(status, status.upper())


def _print_results(result, verbose: bool) -> None:
    for item in result.tests:
        print(f"{_status_label(item.status):6} {item.case.nodeid}  ({item.duration_ms:.1f} ms)")
        if verbose and item.case.params:
            print(f"       params: {item.case.params!r}")
        if item.status in {"failed", "error"} and item.failure:
            print(f"       {item.failure.message.splitlines()[0]}")
            if item.failure.location:
                print(f"       at {item.failure.location}")
        if item.status == "skipped" and item.skip_reason:
            print(f"       reason: {item.skip_reason}")
        if item.status == "xfailed" and item.xfail_reason:
            print(f"       xfail: {item.xfail_reason}")


def _print_summary(result) -> None:
    s = result.summary
    print()
    print(
        f"{s['total']} cases: {s['passed']} passed, {s['failed']} failed, "
        f"{s['error']} errors, {s['skipped']} skipped, {s['xfailed']} xfailed, "
        f"{s['xpassed']} xpassed, {s['deselected']} deselected, "
        f"{s['retried']} retried, {s['flaky']} flaky"
    )
    print(f"duration: {result.duration_ms / 1000:.2f}s · exit code: {result.exit_code}")


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        prog="minipytest",
        description="A small, self-contained pytest-like runner used in ai-qa-lab module 02.",
    )
    parser.add_argument("paths", nargs="+", help="test file or directory paths")
    parser.add_argument("--json", dest="json_path", help="write a JSON report")
    parser.add_argument("--html", dest="html_path", help="write a self-contained HTML report")
    parser.add_argument("-m", "--marker", dest="marker_expr", help="marker expression, e.g. 'smoke and not slow'")
    parser.add_argument("--retry", type=int, default=1, help="global attempts for failed tests (default 1)")
    parser.add_argument("--rootdir", help="root directory for node IDs and conftest discovery")
    parser.add_argument("-v", "--verbose", action="store_true", help="show params and failure headers")
    parser.add_argument("--version", action="version", version=f"minipytest {TOOL_VERSION}")
    args = parser.parse_args(argv)

    try:
        result = run(
            args.paths,
            rootdir=args.rootdir,
            marker_expr=args.marker_expr,
            retry=args.retry,
            command=["minipytest", *((argv if argv is not None else sys.argv[1:]))],
        )
    except UsageError as exc:
        print(f"usage error: {exc}")
        return 2

    _print_results(result, args.verbose)
    _print_summary(result)

    if args.json_path:
        write_json_report(result, Path(args.json_path))
        print(f"json: {args.json_path}")
    if args.html_path:
        write_html_report(result, Path(args.html_path))
        print(f"html: {args.html_path}")

    return result.exit_code
