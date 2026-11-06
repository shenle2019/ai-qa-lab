"""Phase 2 smoke: exercise case management and generation-from-requirement end to end."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parents[1] / "docs" / "phases" / "phase-2" / "smoke-output.json"


def main() -> int:
    report: dict = {"base": BASE, "steps": []}
    with httpx.Client(base_url=BASE, timeout=180.0) as client:
        health = client.get("/health").json()
        report["health"] = health

        projects = client.get("/api/platform/projects").json()
        project = projects[0]
        report["project"] = {"id": project["id"], "name": project["name"]}

        created = client.post(
            "/api/platform/cases",
            json={
                "project_id": project["id"],
                "title": "phase2 冒烟：工单详情返回 404",
                "module": "api",
                "priority": "medium",
                "steps": "1. GET /api/tickets/999999\n2. 断言 status=404",
                "expected": "返回 404",
            },
        )
        created.raise_for_status()
        case = created.json()
        report["steps"].append({"create": created.status_code, "id": case["id"]})

        edited = client.patch(
            f"/api/platform/cases/{case['id']}",
            json={"title": "phase2 冒烟：工单详情不存在返回 404", "priority": "high"},
        )
        edited.raise_for_status()
        report["steps"].append({"patch": edited.status_code, "title": edited.json()["title"]})

        reset = client.post("/api/platform/cases/batch", json={"action": "draft", "ids": [case["id"]]}).json()
        submitted = client.post(
            "/api/platform/cases/batch", json={"action": "submit_review", "ids": [case["id"]]}
        ).json()
        approved = client.post(
            "/api/platform/cases/batch",
            json={"action": "approve", "ids": [case["id"]], "reviewer": "smoke", "comment": "ok"},
        ).json()
        report["steps"].append({"draft": reset, "submit": submitted, "approve": approved})

        reviews = client.get(f"/api/platform/cases/{case['id']}/reviews").json()
        report["reviews"] = {"count": len(reviews), "first": reviews[0] if reviews else None}

        requirements = client.get("/api/platform/requirements").json()
        analyzed = [r for r in requirements if r.get("analysis")]
        if analyzed:
            req = analyzed[0]
            generated = client.post(
                "/api/platform/skills/case.generate/run",
                json={"project_id": req["project_id"], "requirement_id": req["id"], "max_cases": 4},
            )
            report["steps"].append({"generate": generated.status_code, "requirement_id": req["id"]})
            if generated.status_code == 200:
                body = generated.json()["result"]
                report["generated"] = {
                    "model": body["model_name"],
                    "count": len(body["cases"]),
                    "first_titles": [c["title"] for c in body["cases"][:3]],
                    "has_steps": all(bool(c["steps"]) for c in body["cases"]),
                    "statuses": sorted({c["status"] for c in body["cases"]}),
                }
                ids = [c["id"] for c in body["cases"]]
                cleanup = client.post(
                    "/api/platform/cases/batch", json={"action": "delete", "ids": ids}
                ).json()
                report["generated"]["cleanup"] = cleanup
            else:
                report["generated"] = {"error": generated.text}
        else:
            report["generated"] = {"skipped": "no analyzed requirement"}

        removed = client.delete(f"/api/platform/cases/{case['id']}")
        report["steps"].append({"delete": removed.status_code})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
