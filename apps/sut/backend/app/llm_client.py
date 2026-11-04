"""Minimal LLM client with call accounting.

Only an OpenAI-compatible chat completions endpoint is assumed, so DeepSeek
works out of the box and other compatible providers can be added by config.
"""

from __future__ import annotations

import json
import os
import time

import httpx
from sqlalchemy.orm import Session

from . import llm_models


class LLMError(RuntimeError):
    pass


def mask_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}…{value[-4:]}"


def resolve_api_key(config: llm_models.ModelConfig) -> str:
    return config.api_key or os.getenv("DEEPSEEK_API_KEY", "")


def _record(
    db: Session,
    config: llm_models.ModelConfig,
    purpose: str,
    prompt_version: str,
    duration_ms: int,
    status: str,
    *,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    error: str = "",
) -> None:
    db.add(
        llm_models.LLMCall(
            model_id=config.id,
            model_name=config.model_name,
            purpose=purpose,
            prompt_version=prompt_version,
            duration_ms=duration_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            status=status,
            error=error[:1000],
        )
    )
    db.commit()


def chat_json(
    db: Session,
    config: llm_models.ModelConfig,
    messages: list[dict],
    *,
    purpose: str,
    prompt_version: str = "v1",
    timeout: float = 60.0,
    max_tokens: int = 4000,
    temperature: float = 0.0,
) -> dict:
    api_key = resolve_api_key(config)
    if not api_key:
        _record(db, config, purpose, prompt_version, 0, "error", error="missing api key")
        raise LLMError("未配置 API Key")

    url = config.base_url.rstrip("/") + "/chat/completions"
    started = time.perf_counter()
    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": config.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        usage = payload.get("usage", {}) or {}
        _record(
            db,
            config,
            purpose,
            prompt_version,
            int((time.perf_counter() - started) * 1000),
            "ok",
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
        )
        return parsed
    except Exception as exc:  # noqa: BLE001 - surface provider errors to the caller
        _record(
            db,
            config,
            purpose,
            prompt_version,
            int((time.perf_counter() - started) * 1000),
            "error",
            error=str(exc),
        )
        raise LLMError(f"模型调用失败: {exc}") from exc
