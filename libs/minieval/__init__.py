"""minieval: a small LLM evaluation engine with deterministic mock judging."""

from __future__ import annotations

from .dataset import EvalCase, load_jsonl
from .engine import EvalResult, compare_results, evaluate, run_compare
from .judges import DeepSeekJudge, MockJudge, get_judge
from .reporting import write_html_report, write_json_report

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "EvalCase",
    "load_jsonl",
    "MockJudge",
    "DeepSeekJudge",
    "get_judge",
    "evaluate",
    "run_compare",
    "compare_results",
    "EvalResult",
    "write_json_report",
    "write_html_report",
]
