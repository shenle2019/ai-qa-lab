"""Pydantic schemas for the API automation module."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
CASE_KINDS = {"case", "scenario"}
CASE_STATUSES = {"draft", "approved", "disabled"}


class AssetOut(BaseModel):
    id: int
    project_id: int
    name: str
    source: str
    spec_version: str | None = None
    base_url: str | None = None
    endpoint_count: int = 0
    created_at: datetime


class EndpointCreate(BaseModel):
    project_id: int
    asset_id: int | None = None
    method: str = Field(default="GET", max_length=10)
    path: str = Field(min_length=1, max_length=500)
    name: str = Field(default="", max_length=200)
    module: str = Field(default="未分组", max_length=80)
    summary: str | None = None
    params: list[dict[str, Any]] = Field(default_factory=list)
    body: dict[str, Any] = Field(default_factory=dict)
    responses: list[dict[str, Any]] = Field(default_factory=list)


class EndpointUpdate(BaseModel):
    method: str | None = Field(default=None, max_length=10)
    path: str | None = Field(default=None, min_length=1, max_length=500)
    name: str | None = Field(default=None, max_length=200)
    module: str | None = Field(default=None, max_length=80)
    summary: str | None = None
    params: list[dict[str, Any]] | None = None
    body: dict[str, Any] | None = None
    responses: list[dict[str, Any]] | None = None


class EndpointOut(BaseModel):
    id: int
    project_id: int
    asset_id: int | None = None
    method: str
    path: str
    name: str
    module: str
    summary: str | None = None
    params: list[dict[str, Any]] = Field(default_factory=list)
    body: dict[str, Any] = Field(default_factory=dict)
    responses: list[dict[str, Any]] = Field(default_factory=list)
    source: str
    case_count: int = 0
    created_at: datetime
    updated_at: datetime


class ImportSpecIn(BaseModel):
    project_id: int
    spec: str = Field(min_length=1)
    name: str | None = Field(default=None, max_length=200)


class CaseCreate(BaseModel):
    project_id: int
    endpoint_id: int | None = None
    kind: Literal["case", "scenario"] = "case"
    title: str = Field(min_length=1, max_length=200)
    module: str = Field(default="未分组", max_length=80)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    expected: str | None = None
    status: Literal["draft", "approved", "disabled"] = "draft"


class CaseUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    module: str | None = Field(default=None, max_length=80)
    steps: list[dict[str, Any]] | None = None
    expected: str | None = None
    status: Literal["draft", "approved", "disabled"] | None = None


class CaseOut(BaseModel):
    id: int
    project_id: int
    endpoint_id: int | None = None
    kind: str
    title: str
    module: str
    steps: list[dict[str, Any]] = Field(default_factory=list)
    expected: str | None = None
    status: str
    source: str
    prompt_version: str | None = None
    created_at: datetime


class RunOut(BaseModel):
    id: int
    project_id: int
    case_id: int | None = None
    endpoint_id: int | None = None
    kind: str
    title: str
    status: str
    status_code: int | None = None
    duration_ms: int = 0
    request: dict[str, Any] = Field(default_factory=dict)
    response: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    ai_root_cause: str | None = None
    created_at: datetime


class DebugIn(BaseModel):
    base_url: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    body: Any = None
    expect_status: int | None = None


class GenerateCasesIn(BaseModel):
    endpoint_id: int
    count: int = Field(default=5, ge=1, le=15)
    kb_id: int | None = None
    model_id: int | None = None


class GenerateScenarioIn(BaseModel):
    project_id: int
    endpoint_ids: list[int] = Field(min_length=1, max_length=12)
    goal: str = Field(default="", max_length=2000)
    model_id: int | None = None
