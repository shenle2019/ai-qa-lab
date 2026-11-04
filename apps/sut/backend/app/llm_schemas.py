from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ModelConfigCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    provider: str = "deepseek"
    base_url: str = "https://api.deepseek.com"
    model_name: str = "deepseek-chat"
    api_key: str = ""
    enabled: bool = True


class ModelConfigUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    provider: str | None = None
    base_url: str | None = None
    model_name: str | None = None
    api_key: str | None = None
    enabled: bool | None = None


class ModelConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    provider: str
    base_url: str
    model_name: str
    enabled: bool
    has_api_key: bool
    api_key_masked: str
    created_at: datetime


class LLMCallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    model_id: int | None
    model_name: str
    purpose: str
    prompt_version: str
    duration_ms: int
    prompt_tokens: int
    completion_tokens: int
    status: str
    error: str
    created_at: datetime


class ModelTestResult(BaseModel):
    ok: bool
    latency_ms: int
    message: str
