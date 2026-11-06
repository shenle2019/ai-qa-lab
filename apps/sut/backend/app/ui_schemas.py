"""Request/response models for UI automation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

STATUSES = {"draft", "ready", "archived"}


class UiCaseCreate(BaseModel):
    project_id: int
    title: str = Field(min_length=1, max_length=200)
    module: str = Field(default="未分组", max_length=80)
    base_url: str = Field(default="", max_length=500)
    env: dict[str, str] = Field(default_factory=dict)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "draft"


class UiCaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    module: str | None = Field(default=None, max_length=80)
    base_url: str | None = Field(default=None, max_length=500)
    env: dict[str, str] | None = None
    steps: list[dict[str, Any]] | None = None
    status: str | None = None


class UiCaseOut(BaseModel):
    id: int
    project_id: int
    title: str
    module: str
    kind: str
    base_url: str
    env: dict[str, str]
    steps: list[dict[str, Any]]
    status: str
    source: str
    prompt_version: str | None = None
    note: str | None = None
    created_at: datetime
    updated_at: datetime


class UiRunOut(BaseModel):
    id: int
    project_id: int
    case_id: int | None = None
    title: str
    status: str
    duration_ms: int
    steps: list[dict[str, Any]]
    screenshot: str | None = None
    error: str | None = None
    created_at: datetime


class ExploreIn(BaseModel):
    project_id: int
    url: str = Field(min_length=4, max_length=500)
    goal: str = Field(min_length=2, max_length=1000)
    env: dict[str, str] = Field(default_factory=dict)
    model_id: int | None = None
    save: bool = True


class ExploreOut(BaseModel):
    url: str
    title: str
    nodes: int
    steps: list[dict[str, Any]]
    reasoning: str = ""
    case: UiCaseOut | None = None


class ChatIn(BaseModel):
    url: str = Field(min_length=4, max_length=500)
    question: str = Field(min_length=1, max_length=800)
    env: dict[str, str] = Field(default_factory=dict)
    model_id: int | None = None


class ChatOut(BaseModel):
    reply: str
    title: str
    url: str
