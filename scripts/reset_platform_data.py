"""Delete every row from the platform tables (local maintenance helper).

Run with the API server stopped so SQLite is not writing concurrently.
Keep the schema; only data is removed.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "sut" / "backend"))

from app.db import Base, SessionLocal  # noqa: E402
from app import (  # noqa: F401,E402  (import registers the tables)
    api_models,
    environment_models,
    knowledge_models,
    llm_models,
    platform_models,
    project_content_models,
    requirement_models,
    ui_models,
    users_api,
)


def main() -> int:
    with SessionLocal() as session:
        total = 0
        for table in reversed(Base.metadata.sorted_tables):
            removed = session.execute(table.delete()).rowcount or 0
            if removed:
                print(f"{table.name}: {removed}")
            total += removed
        session.commit()
    print("removed rows:", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
