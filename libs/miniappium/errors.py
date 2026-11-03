"""Errors raised by miniappium."""

from __future__ import annotations


class MiniAppiumError(Exception):
    """Base class."""


class DeviceNotFound(MiniAppiumError):
    """No Android device or emulator is connected."""


class WaitTimeout(MiniAppiumError):
    """An element did not appear in time."""


class ExpectationError(AssertionError):
    """An expectation failed."""
