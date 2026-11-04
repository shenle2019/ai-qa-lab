"""Time helper.

SQLite stores naive datetimes, so write UTC values without tzinfo to keep
reads consistent across environments. Callers that need an explicit zone
should format on the boundary.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
