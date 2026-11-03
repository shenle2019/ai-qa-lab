from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    created_at: datetime


class CaseCreate(BaseModel):
    project_id: int
    title: str = Field(min_length=1, max_length=200)
    module: str = "api"
    priority: Literal["low", "medium", "high"] = "medium"
    steps: str = ""
    expected: str = ""


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    title: str
    module: str
    priority: str
    steps: str
    expected: str


class PlanCreate(BaseModel):
    project_id: int
    name: str = Field(min_length=1, max_length=160)


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    name: str
    status: str
    created_at: datetime


class ResultIn(BaseModel):
    case_id: int | None = None
    case_name: str = ""
    status: Literal["passed", "failed", "error", "skipped", "xfailed", "xpassed"]
    duration_ms: int = 0
    message: str = ""


class ResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    execution_id: int
    case_id: int | None
    case_name: str
    status: str
    duration_ms: int
    message: str


class ExecutionCreate(BaseModel):
    results: list[ResultIn]


class ExecutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    plan_id: int
    status: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_ms: int
    started_at: datetime
    results: list[ResultOut] = []


class DefectCreate(BaseModel):
    project_id: int
    title: str = Field(min_length=1, max_length=200)
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    status: Literal["open", "fixed", "closed"] = "open"
    execution_id: int | None = None
    case_id: int | None = None


class DefectUpdate(BaseModel):
    status: Literal["open", "fixed", "closed"]


class DefectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    execution_id: int | None
    case_id: int | None
    title: str
    severity: str
    status: str
    created_at: datetime


class SummaryOut(BaseModel):
    projects: int
    cases: int
    plans: int
    executions: int
    defects: int
    open_defects: int
    pass_rate: float


class ImportRequest(BaseModel):
    plan_id: int | None = None
    report: dict
