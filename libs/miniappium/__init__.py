"""miniappium: a small ADB/UIAutomator client for Android UI automation."""

from __future__ import annotations

from .assertions import expect
from .device import Device, Element, list_devices
from .errors import DeviceNotFound, ExpectationError, MiniAppiumError, WaitTimeout

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Device",
    "Element",
    "list_devices",
    "expect",
    "MiniAppiumError",
    "DeviceNotFound",
    "WaitTimeout",
    "ExpectationError",
]
