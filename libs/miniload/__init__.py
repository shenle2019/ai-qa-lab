"""miniload: a small load-testing engine with thresholds and HTML reports."""

from __future__ import annotations

from .engine import LoadResult, Scenario, run_load
from .reporting import write_html_report, write_json_report

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Scenario",
    "LoadResult",
    "run_load",
    "write_json_report",
    "write_html_report",
]
