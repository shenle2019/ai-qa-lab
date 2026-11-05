"""Minimal service-key authentication for write endpoints in production.

Read endpoints stay public so the demo site can be browsed. Every non-GET
request under /api/ requires `Authorization: Bearer <APP_API_KEY>` or
`X-API-Key: <APP_API_KEY>` when APP_ENV=production.

A few read-only operations use POST for payload convenience. They are listed
in READ_ONLY_POST_PATHS so a visitor can query without holding the key; those
handlers must not write to the database.
"""

import hmac

from fastapi import Request
from fastapi.responses import JSONResponse

from . import settings

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
READ_ONLY_POST_PATHS = {"/api/kb/query"}


def extract_key(request: Request) -> str:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return request.headers.get("x-api-key", "").strip()


async def auth_guard(request: Request, call_next):
    if (
        settings.is_production()
        and request.method not in SAFE_METHODS
        and request.url.path.startswith("/api/")
        and request.url.path not in READ_ONLY_POST_PATHS
    ):
        configured = settings.app_api_key()
        supplied = extract_key(request)
        if not configured or not supplied or not hmac.compare_digest(configured, supplied):
            return JSONResponse(
                status_code=401,
                content={"detail": "unauthorized", "request_id": getattr(request.state, "request_id", "")},
                headers={"WWW-Authenticate": "Bearer"},
            )
    return await call_next(request)
