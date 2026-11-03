"""Simple auto-waiting expectations for Android elements."""

from __future__ import annotations

import time

from .device import Element
from .errors import ExpectationError


class Expectation:
    def __init__(self, actual: Element) -> None:
        self.actual = actual

    def to_be_visible(self, timeout: float = 5.0) -> "Expectation":
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.actual.is_visible():
                return self
            time.sleep(0.1)
        raise ExpectationError(f"element is not visible: {self.actual!r}")

    def to_have_text(self, expected: str, timeout: float = 5.0) -> "Expectation":
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.actual.text == expected:
                return self
            time.sleep(0.1)
        raise ExpectationError(f"expected text {expected!r}, actual={self.actual.text!r}")

    def to_contain_text(self, expected: str, timeout: float = 5.0) -> "Expectation":
        deadline = time.time() + timeout
        while time.time() < deadline:
            if expected in self.actual.text:
                return self
            time.sleep(0.1)
        raise ExpectationError(f"expected text to contain {expected!r}, actual={self.actual.text!r}")


def expect(actual: Element) -> Expectation:
    return Expectation(actual)
