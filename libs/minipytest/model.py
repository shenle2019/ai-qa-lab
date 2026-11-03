"""Core data model for collection, execution, and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .markers import Mark


@dataclass(frozen=True)
class FixtureDef:
    name: str
    func: Callable[..., Any]
    scope: str = "function"
    autouse: bool = False
    source: str = ""


@dataclass
class Case:
    nodeid: str
    path: Path
    name: str
    func: Callable[..., Any]
    params: dict[str, Any] = field(default_factory=dict)
    marks: tuple[Mark, ...] = ()
    cls: type | None = None
    class_name: str | None = None
    fixtures: tuple[FixtureDef, ...] = ()
    param_id: str = ""


@dataclass
class Failure:
    message: str
    phase: str
    type: str
    traceback: str = ""
    location: str = ""
    expected: Any = None
    actual: Any = None
    diff: str = ""


@dataclass
class Attempt:
    number: int
    status: str
    duration_ms: float
    failure: Failure | None = None


@dataclass
class FixtureTiming:
    name: str
    scope: str
    phase: str
    duration_ms: float
    status: str = "ok"


@dataclass
class CaseResult:
    case: Case
    status: str
    phase: str
    duration_ms: float
    attempts: list[Attempt] = field(default_factory=list)
    failure: Failure | None = None
    skip_reason: str | None = None
    xfail_reason: str | None = None
    fixtures: list[FixtureTiming] = field(default_factory=list)
    teardown_errors: list[Failure] = field(default_factory=list)


@dataclass
class CollectionError:
    path: str
    message: str
    traceback: str = ""


@dataclass
class CollectResult:
    cases: list[Case] = field(default_factory=list)
    errors: list[CollectionError] = field(default_factory=list)


@dataclass
class RunResult:
    rootdir: Path
    command: list[str]
    started_at: str
    duration_ms: float
    tests: list[CaseResult]
    summary: dict[str, int]
    collection_errors: list[CollectionError] = field(default_factory=list)
    finalization_errors: list[Failure] = field(default_factory=list)
    deselected: int = 0
    exit_code: int = 0
