"""Shared LLM helpers for builtin skills."""

from __future__ import annotations

from ..registry import SkillError
from ... import llm_models

DEFAULT_PROMPT_VERSION = "v1"


def resolve_model(db, model_id=None):
    """Pick the requested model, else the first enabled chat model."""
    if model_id is not None:
        config = db.get(llm_models.ModelConfig, int(model_id))
        if config is None:
            raise SkillError("model not found", status_code=404)
        return config
    config = (
        db.query(llm_models.ModelConfig)
        .filter(
            llm_models.ModelConfig.enabled.is_(True),
            llm_models.ModelConfig.kind == "chat",
        )
        .order_by(llm_models.ModelConfig.id)
        .first()
    )
    if config is None:
        # Older rows predate the kind column; fall back to any enabled model.
        config = (
            db.query(llm_models.ModelConfig)
            .filter(llm_models.ModelConfig.enabled.is_(True))
            .order_by(llm_models.ModelConfig.id)
            .first()
        )
    if config is None or not config.enabled:
        raise SkillError("没有启用的模型，请先在「系统 AI 配置」里添加")
    return config


def require_db(ctx):
    db = ctx.get("db")
    if db is None:
        raise SkillError("db session missing", status_code=500)
    return db
