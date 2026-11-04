"""Runtime settings read from environment variables.

Kept dependency-free so tests can change env vars without reloading modules.
"""

import os

PRODUCTION_VALUES = {"production", "prod"}


def app_env() -> str:
    return os.getenv("APP_ENV", "development").strip().lower()


def is_production() -> bool:
    return app_env() in PRODUCTION_VALUES


def app_api_key() -> str:
    return os.getenv("APP_API_KEY", "")


def docs_enabled() -> bool:
    return not is_production()


def seed_enabled() -> bool:
    return os.getenv("SEED_DEMO") == "1"


def cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def llm_rate_limit_per_hour() -> int:
    try:
        return int(os.getenv("LLM_RATE_LIMIT_PER_HOUR", "20" if is_production() else "1000"))
    except ValueError:
        return 20 if is_production() else 1000
