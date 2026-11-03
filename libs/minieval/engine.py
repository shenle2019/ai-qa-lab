"""Evaluation engine and baseline/candidate comparison."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .dataset import EvalCase
from .judges import Judge

METRIC_NAMES = (
    "answer_relevance",
    "faithfulness",
    "context_precision",
    "context_recall",
    "correctness",
    "overall",
)


@dataclass
class EvalResult:
    cases: list[dict[str, Any]]
    summary: dict[str, float]
    threshold: float
    passed: bool
    failures: list[str]
    judge: str
    started_at: str


def evaluate(cases: list[EvalCase], judge: Judge, *, threshold: float = 0.7) -> EvalResult:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for case in cases:
        scores = judge.score(case)
        for key in METRIC_NAMES:
            scores.setdefault(key, 0.0)
        rows.append(
            {
                "id": case.id,
                "input": case.input,
                "actual_output": case.actual_output,
                "expected_output": case.expected_output,
                "context": case.context,
                "scores": scores,
            }
        )
        if scores["overall"] < threshold:
            failures.append(case.id)

    summary: dict[str, float] = {}
    for key in METRIC_NAMES:
        summary[key] = round(sum(row["scores"][key] for row in rows) / len(rows), 4) if rows else 0.0

    return EvalResult(
        cases=rows,
        summary=summary,
        threshold=threshold,
        passed=bool(rows) and summary["overall"] >= threshold,
        failures=failures,
        judge=judge.name,
        started_at=datetime.now().isoformat(timespec="seconds"),
    )


def compare_results(baseline: EvalResult, candidate: EvalResult) -> dict[str, Any]:
    delta = {
        key: round(candidate.summary[key] - baseline.summary[key], 4)
        for key in METRIC_NAMES
    }
    return {
        "baseline": baseline.summary,
        "candidate": candidate.summary,
        "delta": delta,
        "improved": delta["overall"] > 0,
    }


def run_compare(cases: list[EvalCase], judge: Judge, *, threshold: float = 0.7):
    baseline_cases = [
        EvalCase(
            id=case.id,
            input=case.input,
            actual_output=case.baseline_output or case.actual_output,
            expected_output=case.expected_output,
            context=case.context,
            baseline_output=None,
        )
        for case in cases
    ]
    baseline = evaluate(baseline_cases, judge, threshold=threshold)
    candidate = evaluate(cases, judge, threshold=threshold)
    return baseline, candidate, compare_results(baseline, candidate)
