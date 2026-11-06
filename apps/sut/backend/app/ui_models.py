"""Persistence for UI automation: cases and execution records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base
from .timeutils import utcnow


class UiCase(Base):
    """One UI case: a list of browser steps plus the localStorage it needs."""

    __tablename__ = "ui_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("platform_projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    module: Mapped[str] = mapped_column(String(80), default="未分组")
    kind: Mapped[str] = mapped_column(String(12), default="case")
    base_url: Mapped[str] = mapped_column(String(500), default="")
    env_json: Mapped[str] = mapped_column(Text, default="{}")
    steps_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True)
    source: Mapped[str] = mapped_column(String(16), default="manual")
    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class UiRun(Base):
    """One UI execution: per-step results plus a failure screenshot."""

    __tablename__ = "ui_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("platform_projects.id"), index=True)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("ui_cases.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(16), default="passed", index=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    steps_json: Mapped[str] = mapped_column(Text, default="[]")
    screenshot: Mapped[str | None] = mapped_column(String(300), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
