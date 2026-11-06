"""Phase 4 demo data: import a real spec, debug, generate cases and a scenario."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
PROJECT_ID = 2
SUT = "http://127.0.0.1:8000"

PROJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "项目 ID"},
        "name": {"type": "string", "description": "项目名称"},
        "description": {"type": "string", "description": "项目描述"},
    },
}

SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "AI 测试平台 API", "version": "1.2.0"},
    "servers": [{"url": SUT}],
    "tags": [{"name": "项目管理"}],
    "paths": {
        "/api/platform/summary": {
            "get": {
                "summary": "平台概览统计",
                "tags": ["项目管理"],
                "responses": {
                    "200": {
                        "description": "ok",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "projects": {"type": "integer"},
                                        "cases": {"type": "integer"},
                                        "plans": {"type": "integer"},
                                        "executions": {"type": "integer"},
                                        "defects": {"type": "integer"},
                                        "pass_rate": {"type": "number"},
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/api/platform/projects": {
            "get": {
                "summary": "查询项目列表",
                "tags": ["项目管理"],
                "responses": {
                    "200": {
                        "description": "ok",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": PROJECT_SCHEMA,
                                    "description": "直接返回项目数组，外面没有 data 包装",
                                }
                            }
                        },
                    }
                },
            },
            "post": {
                "summary": "创建项目",
                "tags": ["项目管理"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {"type": "string", "description": "项目名称，同名会复用"},
                                    "description": {"type": "string", "description": "一句话描述"},
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "201": {
                        "description": "创建成功，直接返回项目对象",
                        "content": {"application/json": {"schema": PROJECT_SCHEMA}},
                    },
                    "200": {
                        "description": "同名复用，直接返回已有项目对象",
                        "content": {"application/json": {"schema": PROJECT_SCHEMA}},
                    },
                },
            },
        },
        "/api/platform/projects/{project_id}": {
            "get": {
                "summary": "查询项目详情",
                "tags": ["项目管理"],
                "parameters": [
                    {
                        "name": "project_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "直接返回项目对象",
                        "content": {"application/json": {"schema": PROJECT_SCHEMA}},
                    },
                    "404": {"description": "missing"},
                },
            }
        },
    },
}


def call(method: str, path: str, **kwargs):
    response = httpx.request(method, f"{BASE}{path}", timeout=240, **kwargs)
    return response


def cleanup_scenario_projects() -> int:
    """The scenario creates 自动化测试项目; drop it so 201 is repeatable."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "sut" / "backend"))
    from app import platform_models as pm  # noqa: PLC0415
    from app.db import SessionLocal  # noqa: PLC0415

    removed = 0
    with SessionLocal() as session:
        rows = session.query(pm.Project).filter(pm.Project.name.like("%自动化测试项目%")).all()
        for row in rows:
            session.query(pm.TestCase).filter(pm.TestCase.project_id == row.id).delete()
            session.delete(row)
            removed += 1
        session.commit()
    return removed


def main() -> int:
    out: dict = {}
    out["cleaned_projects"] = cleanup_scenario_projects()

    assets = call("GET", f"/api/platform/api-assets?project_id={PROJECT_ID}").json()
    if assets:
        print("已有接口资产，跳过导入")
        out["import"] = {"skipped": True, "existing": len(assets)}
    else:
        imported = call(
            "POST",
            "/api/platform/api-assets/import",
            json={"project_id": PROJECT_ID, "spec": json.dumps(SPEC, ensure_ascii=False)},
        )
        print("import", imported.status_code, imported.text[:200])
        out["import"] = imported.json()

    endpoints = call("GET", f"/api/platform/api-endpoints?project_id={PROJECT_ID}").json()
    print("endpoints", len(endpoints))
    out["endpoints"] = [{"id": e["id"], "method": e["method"], "path": e["path"]} for e in endpoints]

    summary_ep = next(e for e in endpoints if e["path"] == "/api/platform/summary")
    projects_ep = next(
        e for e in endpoints if e["path"] == "/api/platform/projects" and e["method"] == "GET"
    )
    create_ep = next(
        e for e in endpoints if e["path"] == "/api/platform/projects" and e["method"] == "POST"
    )
    detail_ep = next(e for e in endpoints if e["path"] == "/api/platform/projects/{project_id}")

    debug = call(
        "POST",
        f"/api/platform/api-endpoints/{summary_ep['id']}/debug",
        json={"base_url": SUT, "expect_status": 200},
    )
    print("debug", debug.status_code, debug.json().get("status"), debug.json().get("status_code"))
    out["debug"] = {
        "status": debug.json().get("status"),
        "status_code": debug.json().get("status_code"),
        "run_id": debug.json().get("id"),
    }

    kb_id = None
    kbs = call("GET", f"/api/platform/knowledge-bases?project_id={PROJECT_ID}").json()
    if kbs:
        kb_id = kbs[0]["id"]

    existing = call("GET", f"/api/platform/api-cases?project_id={PROJECT_ID}").json()
    existing_cases = [item for item in existing if item["kind"] == "case"]
    existing_scen = [item for item in existing if item["kind"] == "scenario"]

    if existing_cases:
        out["generated"] = {"skipped": True, "ids": [item["id"] for item in existing_cases]}
    else:
        generated = call(
            "POST",
            "/api/platform/api-cases/generate",
            json={"endpoint_id": projects_ep["id"], "count": 4, "kb_id": kb_id},
        )
        print("generate cases", generated.status_code, generated.text[:300])
        if generated.status_code == 200:
            body = generated.json()
            out["generated"] = {
                "count": body["count"],
                "used_knowledge": body.get("used_knowledge"),
                "titles": [item["title"] for item in body["cases"]],
                "ids": [item["id"] for item in body["cases"]],
            }
            first = body["cases"][0]
            run = call("POST", f"/api/platform/api-cases/{first['id']}/run")
            print("run case", run.status_code, run.json().get("status"), run.json().get("error"))
            out["case_run"] = {
                "id": first["id"],
                "status": run.json().get("status"),
                "error": run.json().get("error"),
            }

    scenario_id = existing_scen[0]["id"] if existing_scen else None
    if scenario_id is None:
        scenario = call(
            "POST",
            "/api/platform/api-cases/generate-scenario",
            json={
                "project_id": PROJECT_ID,
                "endpoint_ids": [create_ep["id"], detail_ep["id"]],
                "goal": "创建一个项目，然后按返回的 id 查询项目详情，确认名称一致",
            },
        )
        print("generate scenario", scenario.status_code, scenario.text[:300])
        if scenario.status_code == 200:
            body = scenario.json()
            scenario_id = body["id"]
            out["scenario"] = {"id": body["id"], "title": body["title"], "steps": len(body["steps"])}
    if scenario_id is not None:
        run = call("POST", f"/api/platform/api-cases/{scenario_id}/run")
        print("run scenario", run.status_code, run.json().get("status"), run.json().get("error"))
        out["scenario_run"] = {
            "id": scenario_id,
            "status": run.json().get("status"),
            "error": run.json().get("error"),
            "steps": len(run.json().get("steps") or []),
        }

    looks_failed = [item for item in (out.get("generated", {}).get("ids") or [])]
    for case_id in looks_failed[1:]:
        call("POST", f"/api/platform/api-cases/{case_id}/run")

    runs = call("GET", f"/api/platform/api-runs?project_id={PROJECT_ID}&limit=20").json()
    out["run_total"] = len(runs)
    out["failed_runs"] = [item["id"] for item in runs if item["status"] == "failed"]

    with open("docs/phases/phase-4/seed-output.json", "w", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
