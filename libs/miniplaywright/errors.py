"""Errors raised by miniplaywright."""

from __future__ import annotations


class MiniPlaywrightError(Exception):
    """Base class."""


class CDPError(MiniPlaywrightError):
    """A Chrome DevTools Protocol call failed."""


class WaitTimeout(MiniPlaywrightError):
    """A selector or condition did not become ready in time."""


class ExpectationError(AssertionError):
    """An expectation failed after polling."""
