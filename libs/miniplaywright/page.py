"""A small page/locator API on top of CDP."""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any

from .cdp import CDPConnection
from .errors import CDPError, WaitTimeout


def _js(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


class Locator:
    def __init__(self, page: "Page", selector: str) -> None:
        self.page = page
        self.selector = selector

    def wait_for(self, timeout: float = 10.0) -> "Locator":
        self.page.wait_for_selector(self.selector, timeout=timeout)
        return self

    def click(self, timeout: float = 10.0) -> "Locator":
        __tracebackhide__ = True
        self.page.click(self.selector, timeout=timeout)
        return self

    def fill(self, value: str, timeout: float = 10.0) -> "Locator":
        __tracebackhide__ = True
        self.page.fill(self.selector, value, timeout=timeout)
        return self

    def text_content(self) -> str | None:
        return self.page.text(self.selector)

    def is_visible(self) -> bool:
        return self.page.is_visible(self.selector)

    def count(self) -> int:
        return self.page.count(self.selector)

    def screenshot(self, path: str | Path) -> Path:
        return self.page.screenshot(path)

    def __repr__(self) -> str:
        return f"Locator({self.selector!r})"


class Page:
    def __init__(self, cdp: CDPConnection, *, width: int = 1440, height: int = 1000) -> None:
        self.cdp = cdp
        self.cdp.send("Page.enable")
        self.cdp.send("Runtime.enable")
        self.set_viewport(width, height)

    def set_viewport(self, width: int, height: int) -> None:
        self.cdp.send(
            "Emulation.setDeviceMetricsOverride",
            {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False},
        )

    def evaluate(self, expression: str, *, await_promise: bool = False) -> Any:
        __tracebackhide__ = True
        result = self.cdp.send(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": await_promise,
                "userGesture": True,
            },
        )
        if "exceptionDetails" in result:
            details = result["exceptionDetails"]
            text = details.get("text", "JavaScript exception")
            exception = details.get("exception", {})
            description = exception.get("description")
            raise CDPError(description or text)
        return result.get("result", {}).get("value")

    def goto(self, url: str, timeout: float = 20.0) -> "Page":
        __tracebackhide__ = True
        result = self.cdp.send("Page.navigate", {"url": url})
        error_text = result.get("errorText")
        if error_text:
            raise CDPError(f"navigation failed: {error_text}")
        self.wait_for_function(
            "document.readyState === 'complete' && document.location.href !== 'about:blank'",
            timeout=timeout,
        )
        return self

    def wait_for_function(self, expression: str, timeout: float = 10.0, interval: float = 0.1) -> Any:
        __tracebackhide__ = True
        deadline = time.time() + timeout
        last_error: Exception | None = None
        while time.time() < deadline:
            try:
                value = self.evaluate(f"Boolean({expression})")
                if value:
                    return value
            except Exception as exc:
                last_error = exc
            time.sleep(interval)
        suffix = f" last_error={last_error}" if last_error else ""
        raise WaitTimeout(f"condition not met within {timeout}s: {expression}{suffix}")

    def wait_for_selector(self, selector: str, timeout: float = 10.0) -> "Page":
        __tracebackhide__ = True
        self.wait_for_function(f"!!document.querySelector({_js(selector)})", timeout=timeout)
        return self

    def locator(self, selector: str) -> Locator:
        return Locator(self, selector)

    def click(self, selector: str, timeout: float = 10.0) -> "Page":
        self.wait_for_selector(selector, timeout=timeout)
        expression = (
            f"(() => {{ const el = document.querySelector({_js(selector)});"
            " if (!el) return false; el.scrollIntoView({block:'center'}); el.click(); return true; })()"
        )
        if not self.evaluate(expression):
            raise CDPError(f"cannot click missing element: {selector}")
        return self

    def fill(self, selector: str, value: str, timeout: float = 10.0) -> "Page":
        self.wait_for_selector(selector, timeout=timeout)
        expression = (
            f"(() => {{ const el = document.querySelector({_js(selector)});"
            " if (!el) return null; el.focus();"
            f" el.value = {_js(value)};"
            " el.dispatchEvent(new Event('input', {bubbles:true}));"
            " el.dispatchEvent(new Event('change', {bubbles:true})); return el.value; })()"
        )
        if self.evaluate(expression) is None:
            raise CDPError(f"cannot fill missing element: {selector}")
        return self

    def text(self, selector: str) -> str | None:
        value = self.evaluate(
            f"(() => {{ const el = document.querySelector({_js(selector)});"
            " return el ? el.innerText : null; })()"
        )
        return str(value).strip() if value is not None else None

    def count(self, selector: str) -> int:
        return int(self.evaluate(f"document.querySelectorAll({_js(selector)}).length") or 0)

    def is_visible(self, selector: str) -> bool:
        value = self.evaluate(
            f"(() => {{ const el = document.querySelector({_js(selector)});"
            " if (!el) return false; const style = getComputedStyle(el);"
            " return el.offsetParent !== null && style.visibility !== 'hidden' && style.display !== 'none'; })()"
        )
        return bool(value)

    def title(self) -> str:
        return str(self.evaluate("document.title") or "")

    def url(self) -> str:
        return str(self.evaluate("document.location.href") or "")

    def screenshot(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        result = self.cdp.send(
            "Page.captureScreenshot",
            {"format": "png", "captureBeyondViewport": False, "fromSurface": True},
        )
        data = result.get("data")
        if not data:
            raise CDPError("screenshot returned no data")
        target.write_bytes(base64.b64decode(data))
        return target

    def wait(self, seconds: float) -> None:
        time.sleep(seconds)
