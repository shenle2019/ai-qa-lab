"""Tiny in-process limiter for LLM-backed endpoints.

Good enough for a single-instance demo; replace with Redis when scaling out.
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from . import settings

_buckets: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_llm_quota(request: Request) -> None:
    if not settings.is_production():
        return
    limit = settings.llm_rate_limit_per_hour()
    if limit <= 0:
        return
    key = _client_ip(request)
    now = time.time()
    bucket = _buckets[key]
    while bucket and now - bucket[0] > 3600:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(status_code=429, detail="LLM quota exceeded, try later")
    bucket.append(now)
