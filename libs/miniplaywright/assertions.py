"""Auto-waiting expectations for pages and locators."""

from __future__ import annotations

import time
from typing import Any

from .errors import ExpectationError
from .page import Locator, Page


class Expectation:
    def __init__(self, actual: Page | Locator) -> None:
        self.actual = actual

    def _poll(self, check, describe: str, timeout: float) -> None:
        __tracebackhide__ = True
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            try:
                if check():
                    return
                last = self._snapshot()
            except Exception as exc:
                last = str(exc)
            time.sleep(0.1)
        raise ExpectationError(f"{describe}; actual={last!r}")

    def _snapshot(self) -> Any:
        if isinstance(self.actual, Page):
            return self.actual.url()
        return self.actual.text_content()

    def to_have_text(self, expected: str, timeout: float = 5.0) -> "Expectation":
        __tracebackhide__ = True
        assert isinstance(self.actual, Locator)
        self._poll(
            lambda: (self.actual.text_content() or "") == expected,
            f"expected text {expected!r}",
            timeout,
        )
        return self

    def to_contain_text(self, expected: str, timeout: float = 5.0) -> "Expectation":
        __tracebackhide__ = True
        assert isinstance(self.actual, Locator)
        self._poll(
            lambda: expected in (self.actual.text_content() or ""),
            f"expected text to contain {expected!r}",
            timeout,
        )
        return self

    def to_be_visible(self, timeout: float = 5.0) -> "Expectation":
        __tracebackhide__ = True
        assert isinstance(self.actual, Locator)
        self._poll(self.actual.is_visible, "expected locator to be visible", timeout)
        return self

    def to_have_count(self, expected: int, timeout: float = 5.0) -> "Expectation":
        __tracebackhide__ = True
        assert isinstance(self.actual, Locator)
        self._poll(
            lambda: self.actual.count() == expected,
            f"expected count {expected}",
            timeout,
        )
        return self

    def to_have_url(self, fragment: str, timeout: float = 5.0) -> "Expectation":
        __tracebackhide__ = True
        assert isinstance(self.actual, Page)
        self._poll(
            lambda: fragment in self.actual.url(),
            f"expected url to contain {fragment!r}",
            timeout,
        )
        return self

    def to_have_title(self, expected: str, timeout: float = 5.0) -> "Expectation":
        __tracebackhide__ = True
        assert isinstance(self.actual, Page)
        self._poll(
            lambda: self.actual.title() == expected,
            f"expected title {expected!r}",
            timeout,
        )
        return self


def expect(actual: Page | Locator) -> Expectation:
    return Expectation(actual)
