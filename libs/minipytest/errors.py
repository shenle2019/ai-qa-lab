"""Exceptions shared by the mini pytest runner."""

from __future__ import annotations

from typing import Any


class MiniPytestError(Exception):
    """Base class for framework errors."""


class UsageError(MiniPytestError):
    """Invalid CLI usage or marker expression."""


class Skipped(Exception):
    """Raised by skip() or a fixture to mark a case as skipped."""

    def __init__(self, reason: str = "") -> None:
        super().__init__(reason)
        self.reason = reason


class AssertionFailure(AssertionError):
    """Rich assertion failure with values and an optional diff."""

    def __init__(
        self,
        message: str,
        *,
        expected: Any = None,
        actual: Any = None,
        operator: str = "assert",
        diff: str = "",
        location: str = "",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.expected = expected
        self.actual = actual
        self.operator = operator
        self.diff = diff
        self.location = location


class FixtureError(MiniPytestError):
    """A fixture failed during setup or teardown."""

    def __init__(self, name: str, phase: str, original: BaseException) -> None:
        super().__init__(f"fixture {name!r} failed during {phase}: {original}")
        self.name = name
        self.phase = phase
        self.original = original


class FixtureNotFound(MiniPytestError):
    """A test or fixture requested a fixture that is not defined."""

    def __init__(self, name: str) -> None:
        super().__init__(f"fixture {name!r} not found")
        self.name = name
