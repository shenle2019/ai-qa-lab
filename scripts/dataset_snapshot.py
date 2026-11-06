"""Take a live snapshot of the platform inventory (counts + summary).

Used after extra executions were recorded, so the report shows current numbers
without re-running the whole seed.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "dataset"

LIST_ENDPOINTS = {
    "requirements": "/api/platform/requirements",
    "cases": "/api/platform/cases",
    "plans": "/api/platform/plans",
    "defects": "/api/platform/defects",
    "knowledge_bases": "/api/platform/knowledge-bases",
    "api_assets": "/api/platform/api-assets",
    "api_endpoints": "/api/platform/api-endpoints",
    "api_cases": "/api/platform/api-cases",
    "api_runs": "/api/platform/api-runs",
    "ui_cases": "/api/platform/ui-cases",
    "users": "/api/platform/users",
    "models": "/api/platform/models",
}

PER_PROJECT = {
    "environments": "/api/platform/environments",
    "modules": "/api/platform/modules",
    "members": "/api/platform/members",
    "ui_runs": "/api/platform/ui-runs",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--key", default="")
    parser.add_argument("--label", default="local")
    args = parser.parse_args()

    headers = {"X-API-Key": args.key} if args.key else {}
    with httpx.Client(base_url=args.base.rstrip("/"), timeout=120.0, headers=headers) as client:
        projects = client.get("/api/platform/projects").json()
        counts: dict[str, int] = {"projects": len(projects)}
        for key, path in LIST_ENDPOINTS.items():
            response = client.get(path, params={"limit": 500})
            payload = response.json() if response.status_code < 400 else []
            counts[key] = len(payload) if isinstance(payload, list) else 0

        for key, path in PER_PROJECT.items():
            total = 0
            for project in projects:
                response = client.get(path, params={"project_id": project["id"]})
                if response.status_code < 400 and isinstance(response.json(), list):
                    total += len(response.json())
            counts[key] = total

        docs = 0
        for kb in client.get("/api/platform/knowledge-bases").json():
            docs += int(kb.get("document_count") or 0)
        counts["knowledge_documents"] = docs

        summary = client.get("/api/platform/summary").json()

    payload = {
        "label": args.label,
        "base": args.base,
        "elapsed_seconds": 0,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "platform_summary": summary,
        "counts": counts,
        "tests": [],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{args.label}-snapshot-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False))
    print("summary", summary)
    print("written", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
