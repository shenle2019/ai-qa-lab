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
    steps_json: str = "[]"


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    title: str
    module: str
    priority: str
    steps: str
    expected: str
    status: str
    source: str
    prompt_version: str
    steps_json: str


class GenerateCasesRequest(BaseModel):
    project_id: int
    requirement: str = Field(min_length=10, max_length=8000)
    model_id: int | None = None
    max_cases: int = Field(default=5, ge=1, le=20)


class GeneratedCasesOut(BaseModel):
    model_name: str
    prompt_version: str
    cases: list[CaseOut]


class CaseReviewCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    reviewer: str = "local"
    comment: str = ""


class CaseReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    case_id: int
    reviewer: str
    decision: str
    comment: str
    created_at: datetime


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


class ExecutePlanRequest(BaseModel):
    case_ids: list[int] | None = None
    base_url: str | None = None


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
    results_passed: int = 0
    results_failed: int = 0
    results_total: int = 0


class ImportRequest(BaseModel):
    plan_id: int | None = None
    report: dict
