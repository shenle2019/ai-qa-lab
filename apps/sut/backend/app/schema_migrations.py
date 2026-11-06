"""Tiny additive migration helper for SQLite deployments.

`Base.metadata.create_all` creates new tables but never alters existing ones.
The columns below were added after the first release, so existing databases
need an explicit ALTER TABLE. SQLite does not support IF NOT EXISTS on ADD
COLUMN, hence the inspection step.
"""

from sqlalchemy import inspect, text

TABLE_COLUMNS: dict[str, dict[str, str]] = {
    "platform_cases": {
        "status": "VARCHAR(24) DEFAULT 'approved'",
        "source": "VARCHAR(16) DEFAULT 'manual'",
        "prompt_version": "VARCHAR(40) DEFAULT ''",
        "steps_json": "TEXT DEFAULT '[]'",
    },
    "api_runs": {
        "steps_json": "TEXT DEFAULT '[]'",
    },
    "model_configs": {
        "kind": "VARCHAR(20) DEFAULT 'chat'",
    },
}


def ensure_columns(engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        for table, wanted in TABLE_COLUMNS.items():
            if table not in tables:
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, ddl in wanted.items():
                if name in existing:
                    continue
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
