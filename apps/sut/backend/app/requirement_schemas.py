"""Pydantic schemas for requirement management (Phase 1)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

STATUSES = {"draft", "analyzed", "planned"}
PRIORITIES = {"low", "medium", "high", "urgent"}


class RequirementCreate(BaseModel):
    project_id: int
    title: str = Field(min_length=1, max_length=200)
    body: str = ""
    status: str = "draft"
    priority: str = "medium"


class RequirementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = None
    status: str | None = None
    priority: str | None = None


class AttachmentOut(BaseModel):
    id: int
    filename: str
    content_type: str
    size: int
    created_at: datetime


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime


class RequirementOut(BaseModel):
    id: int
    project_id: int
    title: str
    body: str
    status: str
    priority: str
    source_filename: str
    analysis: dict[str, Any] | None = None
    plan: dict[str, Any] | None = None
    attachments: list[AttachmentOut] = []
    messages: list[MessageOut] = []
    created_at: datetime
    updated_at: datetime


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class ChatOut(BaseModel):
    user: MessageOut
    reply: MessageOut


class PlanIn(BaseModel):
    create_plan: bool = True
