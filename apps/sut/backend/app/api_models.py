"""API automation tables: assets, endpoints, cases, runs."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base
from .timeutils import utcnow


class ApiAsset(Base):
    """An imported spec (OpenAPI/Swagger) or a manual bundle."""

    __tablename__ = "api_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("platform_projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(20), default="openapi")
    spec_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    endpoint_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ApiEndpoint(Base):
    """One method + path pair."""

    __tablename__ = "api_endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("platform_projects.id"), index=True)
    asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("api_assets.id"), nullable=True, index=True
    )
    method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(500))
    name: Mapped[str] = mapped_column(String(200), default="")
    module: Mapped[str] = mapped_column(String(80), default="未分组", index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    params_json: Mapped[str] = mapped_column(Text, default="[]")
    body_json: Mapped[str] = mapped_column(Text, default="{}")
    responses_json: Mapped[str] = mapped_column(Text, default="[]")
    source: Mapped[str] = mapped_column(String(20), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )


class ApiCase(Base):
    """A single-interface case or a multi-step scenario."""

    __tablename__ = "api_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("platform_projects.id"), index=True)
    endpoint_id: Mapped[int | None] = mapped_column(
        ForeignKey("api_endpoints.id"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(String(12), default="case", index=True)
    title: Mapped[str] = mapped_column(String(200))
    module: Mapped[str] = mapped_column(String(80), default="未分组")
    steps_json: Mapped[str] = mapped_column(Text, default="[]")
    expected: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="draft", index=True)
    source: Mapped[str] = mapped_column(String(20), default="manual")
    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ApiRun(Base):
    """One execution record: either a debug call or a case run."""

    __tablename__ = "api_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("platform_projects.id"), index=True)
    case_id: Mapped[int | None] = mapped_column(
        ForeignKey("api_cases.id"), nullable=True, index=True
    )
    endpoint_id: Mapped[int | None] = mapped_column(
        ForeignKey("api_endpoints.id"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(String(12), default="debug")
    title: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(16), default="passed", index=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    request_json: Mapped[str] = mapped_column(Text, default="{}")
    response_json: Mapped[str] = mapped_column(Text, default="{}")
    steps_json: Mapped[str] = mapped_column(Text, default="[]")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
