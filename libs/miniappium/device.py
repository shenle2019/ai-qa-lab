"""A small ADB/UIAutomator client. No Appium server required."""

from __future__ import annotations

import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .errors import DeviceNotFound, MiniAppiumError, WaitTimeout

_BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


def _adb_path() -> str:
    return os.getenv("ADB", "adb")


def list_devices() -> list[str]:
    try:
        output = subprocess.run(
            [_adb_path(), "devices"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except FileNotFoundError as exc:
        raise DeviceNotFound("adb not found in PATH") from exc
    devices: list[str] = []
    for line in output.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


class Element:
    def __init__(self, device: "Device", attributes: dict[str, str]) -> None:
        self.device = device
        self.attributes = attributes

    @property
    def text(self) -> str:
        return self.attributes.get("text", "")

    @property
    def resource_id(self) -> str:
        return self.attributes.get("resource-id", "")

    @property
    def content_desc(self) -> str:
        return self.attributes.get("content-desc", "")

    @property
    def class_name(self) -> str:
        return self.attributes.get("class", "")

    @property
    def bounds(self) -> tuple[int, int, int, int] | None:
        match = _BOUNDS_RE.search(self.attributes.get("bounds", ""))
        if not match:
            return None
        return tuple(int(value) for value in match.groups())  # type: ignore[return-value]

    def center(self) -> tuple[int, int] | None:
        bounds = self.bounds
        if not bounds:
            return None
        x1, y1, x2, y2 = bounds
        return (x1 + x2) // 2, (y1 + y2) // 2

    def is_visible(self) -> bool:
        bounds = self.bounds
        return bool(bounds and bounds[2] > bounds[0] and bounds[3] > bounds[1])

    def tap(self) -> "Element":
        center = self.center()
        if not center:
            raise MiniAppiumError(f"element has no bounds: {self.text!r}")
        self.device.tap(*center)
        return self

    def __repr__(self) -> str:
        return f"Element(text={self.text!r}, id={self.resource_id!r})"


class Device:
    def __init__(self, serial: str) -> None:
        self.serial = serial

    @classmethod
    def connect(cls, serial: str | None = None) -> "Device":
        target = serial or os.getenv("ANDROID_SERIAL")
        devices = list_devices()
        if target and target in devices:
            return cls(target)
        if devices:
            return cls(devices[0])
        raise DeviceNotFound("no Android device connected")

    def _run(self, *args: str, binary: bool = False) -> subprocess.CompletedProcess:
        command = [_adb_path(), "-s", self.serial, *args]
        return subprocess.run(
            command,
            capture_output=True,
            text=not binary,
            encoding=None if binary else "utf-8",
            errors=None if binary else "replace",
            timeout=40,
        )

    def shell(self, *args: str) -> str:
        result = self._run("shell", *args)
        if result.returncode != 0:
            raise MiniAppiumError(f"adb shell failed: {result.stderr.strip()}")
        return result.stdout

    def exec_out(self, *args: str) -> bytes:
        result = self._run("exec-out", *args, binary=True)
        if result.returncode != 0:
            raise MiniAppiumError(f"adb exec-out failed: {result.stderr!r}")
        return result.stdout

    def dump(self) -> ET.Element:
        self.shell("uiautomator", "dump", "/sdcard/window.xml")
        raw = self.exec_out("cat", "/sdcard/window.xml")
        return ET.fromstring(raw)

    def find(
        self,
        *,
        text: str | None = None,
        text_contains: str | None = None,
        resource_id: str | None = None,
        content_desc: str | None = None,
        class_name: str | None = None,
        index: int = 0,
    ) -> Element | None:
        root = self.dump()
        matches: list[Element] = []
        for node in root.iter("node"):
            attributes = node.attrib
            if text is not None and attributes.get("text") != text:
                continue
            if text_contains is not None and text_contains not in attributes.get("text", ""):
                continue
            if resource_id is not None and attributes.get("resource-id") != resource_id:
                continue
            if content_desc is not None and attributes.get("content-desc") != content_desc:
                continue
            if class_name is not None and attributes.get("class") != class_name:
                continue
            matches.append(Element(self, dict(attributes)))
        return matches[index] if 0 <= index < len(matches) else None

    def wait_for(
        self,
        *,
        text: str | None = None,
        text_contains: str | None = None,
        resource_id: str | None = None,
        content_desc: str | None = None,
        class_name: str | None = None,
        timeout: float = 10.0,
    ) -> Element:
        deadline = time.time() + timeout
        last_error: Exception | None = None
        while time.time() < deadline:
            try:
                element = self.find(
                    text=text,
                    text_contains=text_contains,
                    resource_id=resource_id,
                    content_desc=content_desc,
                    class_name=class_name,
                )
                if element is not None and element.is_visible():
                    return element
            except Exception as exc:
                last_error = exc
            time.sleep(0.3)
        suffix = f" last_error={last_error}" if last_error else ""
        raise WaitTimeout(f"element not found within {timeout}s{suffix}")

    def tap(self, x: int, y: int) -> "Device":
        self.shell("input", "tap", str(x), str(y))
        return self

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> "Device":
        self.shell("input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms))
        return self

    def input_text(self, text: str) -> "Device":
        # adb input text does not support CJK reliably; use ASCII in demos.
        escaped = text.replace(" ", "%s")
        self.shell("input", "text", escaped)
        return self

    def press_back(self) -> "Device":
        self.shell("input", "keyevent", "4")
        return self

    def press_home(self) -> "Device":
        self.shell("input", "keyevent", "3")
        return self

    def start_activity(self, action: str) -> "Device":
        self.shell("am", "start", "-a", action)
        return self

    def start_settings(self) -> "Device":
        try:
            self.shell("am", "force-stop", "com.android.settings")
        except MiniAppiumError:
            pass
        return self.start_activity("android.settings.SETTINGS")

    def current_activity(self) -> str:
        output = self.shell("dumpsys", "window")
        for line in output.splitlines():
            if "mCurrentFocus" in line:
                return line.strip()
        return ""

    def screenshot(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.exec_out("screencap", "-p"))
        return target

    def model(self) -> str:
        return self.shell("getprop", "ro.product.model").strip()
