"""CLI for minieval."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .dataset import load_jsonl
from .engine import evaluate, run_compare
from .judges import get_judge
from .reporting import write_html_report, write_json_report


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(prog="minieval", description="Small LLM evaluation engine")
    parser.add_argument("--dataset", required=True, help="JSONL dataset path")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--html", dest="html_path")
    parser.add_argument("--threshold", type=float, default=0.7)
    parser.add_argument("--judge", choices=["mock", "deepseek"], default="mock")
    parser.add_argument("--compare", action="store_true", help="compare actual_output with baseline_output")
    args = parser.parse_args(argv)

    cases = load_jsonl(args.dataset)
    judge = get_judge(args.judge)

    if args.compare:
        baseline, candidate, comparison = run_compare(cases, judge, threshold=args.threshold)
        result = candidate
        print(
            f"baseline overall {baseline.summary['overall']:.2f} → "
            f"candidate {candidate.summary['overall']:.2f} (delta {comparison['delta']['overall']:+.2f})"
        )
    else:
        comparison = None
        result = evaluate(cases, judge, threshold=args.threshold)

    print(
        f"{len(result.cases)} cases · judge {result.judge} · "
        f"overall {result.summary['overall']:.2f} · threshold {result.threshold:.2f} · "
        f"{'PASS' if result.passed else 'FAIL'}"
    )
    if result.failures:
        print("failures: " + ", ".join(result.failures))

    if args.json_path:
        write_json_report(result, Path(args.json_path), comparison)
        print(f"json: {args.json_path}")
    if args.html_path:
        write_html_report(result, Path(args.html_path), comparison)
        print(f"html: {args.html_path}")

    return 0 if result.passed else 1
