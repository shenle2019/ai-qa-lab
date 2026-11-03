"""Fluent assertions with expected/actual values and unified diffs."""

from __future__ import annotations

import difflib
import math
import pprint
import re
from typing import Any

from .errors import AssertionFailure, Skipped

_MAX_VALUE_CHARS = 4000


def _pretty(value: Any) -> str:
    text = pprint.pformat(value, width=90, sort_dicts=False)
    if len(text) > _MAX_VALUE_CHARS:
        text = text[:_MAX_VALUE_CHARS] + "... (truncated)"
    return text


def _lines(value: Any) -> list[str]:
    if isinstance(value, str):
        parts = value.splitlines() or [value]
    else:
        parts = pprint.pformat(value, width=90, sort_dicts=False).splitlines()
    return [line if line.endswith("\n") else line + "\n" for line in parts]


def _diff(expected: Any, actual: Any) -> str:
    if expected == actual:
        return ""
    return "".join(
        difflib.unified_diff(
            _lines(expected),
            _lines(actual),
            fromfile="expected",
            tofile="actual",
            lineterm="",
        )
    )


class Assertion:
    """Chainable assertion object returned by assert_that()."""

    def __init__(self, actual: Any, message: str | None = None) -> None:
        self.actual = actual
        self.message = message

    def _fail(self, reason: str, *, expected: Any, actual: Any, operator: str) -> None:
        text = f"{self.message}: {reason}" if self.message else reason
        text += f"\n  expected: {_pretty(expected)}\n  actual:   {_pretty(actual)}"
        raise AssertionFailure(
            text,
            expected=expected,
            actual=actual,
            operator=operator,
            diff=_diff(expected, actual),
        )

    def is_equal_to(self, expected: Any) -> "Assertion":
        if self.actual != expected:
            self._fail("values are not equal", expected=expected, actual=self.actual, operator="==")
        return self

    def is_not_equal_to(self, expected: Any) -> "Assertion":
        if self.actual == expected:
            self._fail("values are equal, but should differ", expected=expected, actual=self.actual, operator="!=")
        return self

    def contains(self, item: Any) -> "Assertion":
        try:
            found = item in self.actual
        except TypeError:
            found = False
        if not found:
            self._fail("value does not contain the expected item", expected=item, actual=self.actual, operator="contains")
        return self

    def does_not_contain(self, item: Any) -> "Assertion":
        try:
            found = item in self.actual
        except TypeError:
            found = False
        if found:
            self._fail("value contains an item that should be absent", expected=f"not {item!r}", actual=self.actual, operator="not contains")
        return self

    def matches(self, pattern: str) -> "Assertion":
        if re.search(pattern, str(self.actual)) is None:
            self._fail("value does not match the pattern", expected=pattern, actual=self.actual, operator="re.search")
        return self

    def is_in(self, container: Any) -> "Assertion":
        try:
            found = self.actual in container
        except TypeError:
            found = False
        if not found:
            self._fail("value is not in the expected container", expected=container, actual=self.actual, operator="in")
        return self

    def is_true(self) -> "Assertion":
        if not self.actual:
            self._fail("value is not truthy", expected=True, actual=self.actual, operator="truthy")
        return self

    def is_false(self) -> "Assertion":
        if self.actual:
            self._fail("value is not falsy", expected=False, actual=self.actual, operator="falsy")
        return self

    def is_none(self) -> "Assertion":
        if self.actual is not None:
            self._fail("value is not None", expected=None, actual=self.actual, operator="is None")
        return self

    def is_not_none(self) -> "Assertion":
        if self.actual is None:
            self._fail("value is None", expected="not None", actual=None, operator="is not None")
        return self

    def has_length(self, expected: int) -> "Assertion":
        try:
            length = len(self.actual)
        except TypeError:
            self._fail("value has no length", expected=expected, actual=self.actual, operator="len")
            return self
        if length != expected:
            self._fail("length does not match", expected=expected, actual=length, operator="len")
        return self

    def is_instance_of(self, expected: type) -> "Assertion":
        if not isinstance(self.actual, expected):
            self._fail("value is not an instance of the expected type", expected=expected, actual=type(self.actual), operator="isinstance")
        return self

    def is_greater_than(self, expected: Any) -> "Assertion":
        if not self.actual > expected:
            self._fail("value is not greater than expected", expected=expected, actual=self.actual, operator=">")
        return self

    def is_greater_or_equal_to(self, expected: Any) -> "Assertion":
        if not self.actual >= expected:
            self._fail("value is not greater than or equal to expected", expected=expected, actual=self.actual, operator=">=")
        return self

    def is_less_than(self, expected: Any) -> "Assertion":
        if not self.actual < expected:
            self._fail("value is not less than expected", expected=expected, actual=self.actual, operator="<")
        return self

    def is_less_or_equal_to(self, expected: Any) -> "Assertion":
        if not self.actual <= expected:
            self._fail("value is not less than or equal to expected", expected=expected, actual=self.actual, operator="<=")
        return self

    def is_close_to(self, expected: float, *, rel_tol: float = 1e-9, abs_tol: float = 0.0) -> "Assertion":
        if not math.isclose(float(self.actual), float(expected), rel_tol=rel_tol, abs_tol=abs_tol):
            self._fail("values are not close enough", expected=expected, actual=self.actual, operator="isclose")
        return self


class RaisesContext:
    def __init__(self, exc_type: type[BaseException], match: str | None = None) -> None:
        self.exc_type = exc_type
        self.match = match
        self.value: BaseException | None = None

    def __enter__(self) -> "RaisesContext":
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any) -> bool:
        if exc_type is None:
            raise AssertionFailure(
                f"expected {self.exc_type.__name__} to be raised, but nothing was raised",
                expected=self.exc_type.__name__,
                actual="no exception",
                operator="raises",
            )
        if not issubclass(exc_type, self.exc_type):
            raise AssertionFailure(
                f"expected {self.exc_type.__name__}, got {exc_type.__name__}: {exc}",
                expected=self.exc_type.__name__,
                actual=exc_type.__name__,
                operator="raises",
            )
        if self.match is not None and re.search(self.match, str(exc)) is None:
            raise AssertionFailure(
                f"exception message does not match {self.match!r}: {exc}",
                expected=self.match,
                actual=str(exc),
                operator="raises match",
            )
        self.value = exc
        return True


def assert_that(actual: Any, message: str | None = None) -> Assertion:
    return Assertion(actual, message=message)


def raises(exc_type: type[BaseException], *, match: str | None = None) -> RaisesContext:
    return RaisesContext(exc_type, match=match)


def fail(message: str) -> None:
    raise AssertionFailure(message)


def skip(reason: str = "") -> None:
    raise Skipped(reason)
