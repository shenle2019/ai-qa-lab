"""Deterministic lexical metrics used by the mock judge."""

from __future__ import annotations

import re
from typing import Iterable

from .dataset import EvalCase

_TOKEN_RE = re.compile(r"[a-z0-9_]+|[一-鿿]")


def tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _containment(source: Iterable[str], target: Iterable[str]) -> float:
    source_set = set(source)
    target_set = set(target)
    if not source_set:
        return 0.0
    return len(source_set & target_set) / len(source_set)


def score_case(case: EvalCase) -> dict[str, float]:
    input_tokens = tokens(case.input)
    actual_tokens = tokens(case.actual_output)
    expected_tokens = tokens(case.expected_output)
    context_tokens = tokens(" ".join(case.context))

    relevance = _containment(input_tokens, actual_tokens)
    faithfulness = _containment(actual_tokens, context_tokens) if context_tokens else 1.0
    context_precision = _containment(expected_tokens, context_tokens) if context_tokens else 0.0
    context_recall = _containment(context_tokens, expected_tokens) if context_tokens else 0.0
    correctness = _containment(expected_tokens, actual_tokens)
    overall = (relevance + faithfulness + context_precision + context_recall + correctness) / 5
    return {
        "answer_relevance": round(relevance, 4),
        "faithfulness": round(faithfulness, 4),
        "context_precision": round(context_precision, 4),
        "context_recall": round(context_recall, 4),
        "correctness": round(correctness, 4),
        "overall": round(overall, 4),
    }
