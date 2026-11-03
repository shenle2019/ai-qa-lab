"""CLI for miniload."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .engine import Scenario, run_load
from .reporting import TOOL_VERSION, write_html_report, write_json_report


def _parse_header(value: str) -> tuple[str, str]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("header must be 'Key: Value'")
    key, val = value.split(":", 1)
    return key.strip(), val.strip()


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(prog="miniload", description="Small load-testing engine")
    parser.add_argument("--url", required=True, help="target URL")
    parser.add_argument("--name", default="load scenario")
    parser.add_argument("--method", default="GET")
    parser.add_argument("--vus", type=int, default=10)
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--ramp-up", type=float, default=0.0)
    parser.add_argument("--p95", type=float, default=None, help="p95 threshold in ms")
    parser.add_argument("--error-rate", type=float, default=None, help="max error rate, e.g. 0.01")
    parser.add_argument("--min-rps", type=float, default=None)
    parser.add_argument("--header", action="append", type=_parse_header, default=[])
    parser.add_argument("--json-body", default=None)
    parser.add_argument("--data", default=None)
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--html", dest="html_path")
    parser.add_argument("--version", action="version", version=f"miniload {TOOL_VERSION}")
    args = parser.parse_args(argv)

    scenario = Scenario(
        name=args.name,
        method=args.method,
        url=args.url,
        headers=dict(args.header),
        json_body=json.loads(args.json_body) if args.json_body else None,
        data=args.data,
    )
    result = run_load(
        scenario,
        vus=args.vus,
        duration=args.duration,
        ramp_up=args.ramp_up,
        p95_ms=args.p95,
        error_rate=args.error_rate,
        min_rps=args.min_rps,
    )

    print(
        f"{result.total} requests · {result.rps:.1f} rps · "
        f"p95 {result.percentiles['p95']}ms · error {result.error_rate:.2%}"
    )
    if result.violations:
        for violation in result.violations:
            print(f"FAIL: {violation}")
    else:
        print("PASS: all thresholds met")

    if args.json_path:
        write_json_report(result, Path(args.json_path))
        print(f"json: {args.json_path}")
    if args.html_path:
        write_html_report(result, Path(args.html_path))
        print(f"html: {args.html_path}")

    return 0 if result.passed else 1
