"""Inject a small, harmless failure set so executions show both outcomes.

Each project gets one API case whose expectation cannot hold (it asks for 500
from an endpoint that returns 200). Running it records a real failed execution,
which is what the AI root-cause feature works on. Nothing is mutated on the
platform side: the request is a GET.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "dataset"


class Api:
    def __init__(self, base: str, key: str = "") -> None:
        self.client = httpx.Client(
            base_url=base.rstrip("/"),
            timeout=180.0,
            headers={"X-API-Key": key} if key else {},
        )

    def request(self, method: str, path: str, **kwargs):
        response = self.client.request(method, path, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path} -> {response.status_code} {response.text[:200]}")
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, **kw):
        return self.request("POST", path, **kw)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--key", default="")
    parser.add_argument("--label", default="local")
    parser.add_argument("--diagnose", type=int, default=0, help="how many failures to send to the LLM")
    args = parser.parse_args()

    api = Api(args.base, args.key)
    projects = api.get("/api/platform/projects")
    results: list[dict] = []
    diagnosed = 0

    for project in projects:
        title = f"{project['name']}-故障注入：概览接口期望 500（实际 200）"
        cases = api.get("/api/platform/api-cases", params={"project_id": project["id"]})
        case = next((item for item in cases if item["title"] == title), None)
        if case is None:
            case = api.post(
                "/api/platform/api-cases",
                json={
                    "project_id": project["id"],
                    "kind": "case",
                    "title": title,
                    "module": "故障注入",
                    "status": "approved",
                    "expected": "status=500",
                    "steps": [
                        {
                            "name": "故意断言服务端故障",
                            "method": "GET",
                            "url": "/api/platform/summary",
                            "expect": {"status": 500},
                        }
                    ],
                },
            )

        run = api.post(f"/api/platform/api-cases/{case['id']}/run", params={"base_url": args.base})
        entry = {
            "project": project["name"],
            "case": case["title"],
            "run_id": run.get("id"),
            "status": run.get("status"),
            "status_code": run.get("status_code"),
            "reason": (run.get("error") or "")[:200],
            "diagnosed": False,
        }

        if args.diagnose and diagnosed < args.diagnose and run.get("id"):
            try:
                detail = api.post(f"/api/platform/api-runs/{run['id']}/diagnose")
                entry["diagnosed"] = True
                entry["ai_root_cause"] = (detail.get("ai_root_cause") or "")[:400]
                diagnosed += 1
            except Exception as exc:  # noqa: BLE001
                entry["diagnose_error"] = str(exc)[:200]

        # Put the failing case into a plan execution so the overview pass rate
        # reflects it (the summary only counts functional plan results).
        try:
            func_title = f"{project['name']}-故障注入：概览用例期望 500（实际 200）"
            func_cases = api.get("/api/platform/cases", params={"project_id": project["id"]})
            func_case = next((item for item in func_cases if item["title"] == func_title), None)
            if func_case is None:
                func_case = api.post(
                    "/api/platform/cases",
                    json={
                        "project_id": project["id"],
                        "title": func_title,
                        # module must be one the executor actually runs; anything
                        # else is reported as "skipped" and never becomes failed.
                        "module": "api",
                        "priority": "high",
                        "steps": "1. GET /api/platform/summary\n2. 断言 status=500",
                        "expected": "status=500",
                        "steps_json": json.dumps(
                            [{"action": "GET", "target": "/api/platform/summary", "data": "", "assert": "status=500"}],
                            ensure_ascii=False,
                        ),
                    },
                )
            elif func_case.get("module") != "api":
                func_case = api.request(
                    "PATCH", f"/api/platform/cases/{func_case['id']}", json={"module": "api"}
                )
            plans = api.get("/api/platform/plans", params={"project_id": project["id"]})
            plan = next((item for item in plans if item["name"] == f"{project['name']} 回归计划"), None)
            if plan:
                api.post(
                    f"/api/platform/plans/{plan['id']}/execute",
                    json={"case_ids": [func_case["id"]], "base_url": args.base},
                )
                for _ in range(12):
                    time.sleep(1.2)
                    rows = api.get("/api/platform/executions", params={"limit": 200})
                    candidates = [row for row in rows if row["plan_id"] == plan["id"]]
                    if not candidates:
                        continue
                    latest = max(candidates, key=lambda row: row["id"])
                    if latest["status"] != "running":
                        entry["plan"] = plan["name"]
                        entry["plan_status"] = latest["status"]
                        entry["plan_failed"] = latest["failed"]
                        break
        except Exception as exc:  # noqa: BLE001
            entry["plan_error"] = str(exc)[:200]

        results.append(entry)

    payload = {
        "label": args.label,
        "base": args.base,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "runs": results,
        "summary": api.get("/api/platform/summary"),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"failures-{args.label}-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    failed = sum(1 for item in results if item["status"] == "failed")
    print(f"runs={len(results)} failed={failed} diagnosed={diagnosed}")
    print("summary", payload["summary"])
    print("written", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
