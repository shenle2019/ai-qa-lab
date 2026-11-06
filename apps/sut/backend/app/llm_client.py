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


KEY_ENV_NAME = "DEEPSEEK_API_KEY"


def mask_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}…{value[-4:]}"


def resolve_api_key(config: llm_models.ModelConfig | None = None) -> str:
    """Keys live only in the environment; the database never stores them."""
    return os.getenv(KEY_ENV_NAME, "")


def key_display() -> str:
    return f"env:{KEY_ENV_NAME}" if resolve_api_key() else ""


def _parse_json(content: str) -> dict:
    """Parse model output that may be wrapped in markdown or extra text."""
    text = (content or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2 and lines[-1].strip().startswith("```"):
            text = "\n".join(lines[1:-1])
        else:
            text = "\n".join(lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _record(
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
    # Use a dedicated session so accounting never commits the caller's
    # business transaction halfway through.
    from .db import SessionLocal

    with SessionLocal() as session:
        session.add(
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
        session.commit()


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
        _record(config, purpose, prompt_version, 0, "error", error="missing api key")
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
        try:
            parsed = _parse_json(content)
        except json.JSONDecodeError as exc:
            finish = payload["choices"][0].get("finish_reason")
            raise LLMError(f"模型返回不是合法 JSON（finish={finish}）: {content[:200]}") from exc
        usage = payload.get("usage", {}) or {}
        _record(
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
            config,
            purpose,
            prompt_version,
            int((time.perf_counter() - started) * 1000),
            "error",
            error=str(exc),
        )
        raise LLMError(f"模型调用失败: {exc}") from exc


def chat_text(
    db: Session,
    config: llm_models.ModelConfig,
    messages: list[dict],
    *,
    purpose: str,
    prompt_version: str = "v1",
    timeout: float = 60.0,
    max_tokens: int = 2000,
    temperature: float = 0.3,
) -> str:
    """Free-form completion (no JSON constraint) for conversational agents."""
    api_key = resolve_api_key(config)
    if not api_key:
        _record(config, purpose, prompt_version, 0, "error", error="missing api key")
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
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"] or ""
        usage = payload.get("usage", {}) or {}
        _record(
            config,
            purpose,
            prompt_version,
            int((time.perf_counter() - started) * 1000),
            "ok",
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
        )
        return content.strip()
    except Exception as exc:  # noqa: BLE001 - surface provider errors to the caller
        _record(
            config,
            purpose,
            prompt_version,
            int((time.perf_counter() - started) * 1000),
            "error",
            error=str(exc),
        )
        raise LLMError(f"模型调用失败: {exc}") from exc
