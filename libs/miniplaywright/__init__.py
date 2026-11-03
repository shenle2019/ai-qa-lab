"""miniplaywright: a small CDP-based browser automation library."""

from __future__ import annotations

from .assertions import expect
from .browser import Browser, launch
from .errors import CDPError, ExpectationError, MiniPlaywrightError, WaitTimeout
from .page import Locator, Page

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "launch",
    "Browser",
    "Page",
    "Locator",
    "expect",
    "MiniPlaywrightError",
    "CDPError",
    "WaitTimeout",
    "ExpectationError",
]
