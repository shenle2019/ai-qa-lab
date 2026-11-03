"""minipytest: a small, clean-room pytest-like runner for ai-qa-lab."""

from __future__ import annotations

from .assertions import assert_that, fail, raises, skip
from .errors import (
    AssertionFailure,
    FixtureError,
    FixtureNotFound,
    MiniPytestError,
    Skipped,
    UsageError,
)
from .fixtures import fixture
from .markers import Mark, parametrize, param, mark
from .model import Case, CaseResult, Failure, RunResult
from .reporting import result_to_dict, write_html_report, write_json_report
from .runner import run

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "fixture",
    "parametrize",
    "param",
    "mark",
    "assert_that",
    "raises",
    "fail",
    "skip",
    "run",
    "write_json_report",
    "write_html_report",
    "result_to_dict",
    "Case",
    "CaseResult",
    "Failure",
    "RunResult",
    "Mark",
    "AssertionFailure",
    "FixtureError",
    "FixtureNotFound",
    "MiniPytestError",
    "Skipped",
    "UsageError",
]
