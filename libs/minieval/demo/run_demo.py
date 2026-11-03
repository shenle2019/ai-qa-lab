from __future__ import annotations

from pathlib import Path

from libs.minieval import get_judge, load_jsonl, run_compare, write_html_report, write_json_report

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "portfolio"
DATASET = ROOT / "libs" / "minieval" / "demo" / "dataset.jsonl"


def main() -> int:
    cases = load_jsonl(DATASET)
    judge = get_judge("mock")
    baseline, candidate, comparison = run_compare(cases, judge, threshold=0.7)

    write_json_report(candidate, OUT / "module-08-llm-report.json", comparison)
    write_html_report(candidate, OUT / "module-08-llm-report.html", comparison)

    print(
        f"baseline {baseline.summary['overall']:.2f} → candidate {candidate.summary['overall']:.2f} "
        f"(delta {comparison['delta']['overall']:+.2f})"
    )
    print(
        f"{len(candidate.cases)} cases · judge {candidate.judge} · "
        f"overall {candidate.summary['overall']:.2f} · threshold {candidate.threshold:.2f} · "
        f"{'PASS' if candidate.passed else 'FAIL'}"
    )
    if candidate.failures:
        print("failures: " + ", ".join(candidate.failures))
    return 0 if candidate.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
