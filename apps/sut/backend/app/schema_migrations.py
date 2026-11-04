"""Tiny additive migration helper for SQLite deployments.

`Base.metadata.create_all` creates new tables but never alters existing ones.
The columns below were added after the first release, so existing databases
need an explicit ALTER TABLE. SQLite does not support IF NOT EXISTS on ADD
COLUMN, hence the inspection step.
"""

from sqlalchemy import inspect, text


CASE_COLUMNS = {
    "status": "VARCHAR(24) DEFAULT 'approved'",
    "source": "VARCHAR(16) DEFAULT 'manual'",
    "prompt_version": "VARCHAR(40) DEFAULT ''",
    "steps_json": "TEXT DEFAULT '[]'",
}


def ensure_columns(engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "platform_cases" not in tables:
        return
    existing = {column["name"] for column in inspector.get_columns("platform_cases")}
    missing = {name: ddl for name, ddl in CASE_COLUMNS.items() if name not in existing}
    if not missing:
        return
    with engine.begin() as connection:
        for name, ddl in missing.items():
            connection.execute(text(f"ALTER TABLE platform_cases ADD COLUMN {name} {ddl}"))
