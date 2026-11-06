"""One-shot end-to-end acceptance run across every phase.

Walks the real platform APIs in the order a tester would use them:

    project -> requirement -> analyze -> plan -> cases
    -> knowledge base -> ingest -> search
    -> openapi import -> debug -> api case -> run
    -> ui explore -> ui case -> run

Writes docs/acceptance/acceptance-output.json and prints a summary.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000/api/platform"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "acceptance" / "acceptance-output.json"

SPEC = {
    "openapi": "3.0.3",
    "info": {"title": "验收演示 API", "version": "1.0.0"},
    "servers": [{"url": "http://127.0.0.1:8000"}],
    "paths": {
        "/api/platform/summary": {
            "get": {
                "tags": ["平台"],
                "summary": "平台汇总",
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
                "tags": ["项目"],
                "summary": "项目列表",
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}, "description": "条数"}
                ],
                "responses": {"200": {"description": "ok"}},
            },
            "post": {
                "tags": ["项目"],
                "summary": "创建项目",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                },
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "ok"},
                    "201": {"description": "created"},
                },
            },
        },
    },
}

REQUIREMENT = """
# 工单导出

## 背景
客服需要把筛选后的工单导出成表格，交给运营做周报。

## 需求
1. 工单列表顶部增加「导出 CSV」按钮，导出当前筛选结果。
2. 导出条数超过 5000 条时提示并转为后台任务，完成后站内信通知。
3. 文件编码 UTF-8 BOM，Excel 直接打开不乱码。
4. 非管理员点击导出提示无权限。

## 约束
单次导出不超过 10 万条；导出任务保留 7 天。
"""


def call(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    response = client.request(method, BASE + path, **kwargs)
    if response.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {response.status_code} {response.text[:300]}")
    return response.json() if response.content else {}


def main() -> int:
    client = httpx.Client(timeout=240)
    steps: list[dict] = []
    started = time.time()

    def note(name: str, **payload) -> None:
        steps.append({"step": name, "ok": True, **payload})
        print(f"[ok] {name} {json.dumps(payload, ensure_ascii=False)[:160]}")

    project = call(client, "POST", "/projects", json={"name": "验收演示项目", "description": "端到端验收"})
    project_id = project["id"]
    note("project.create", id=project_id)

    for old in call(client, "GET", f"/requirements?project_id={project_id}"):
        if old["title"] == "工单导出":
            client.delete(f"{BASE}/requirements/{old['id']}")

    requirement = call(
        client,
        "POST",
        "/requirements",
        json={"project_id": project_id, "title": "工单导出", "body": REQUIREMENT, "priority": "high"},
    )
    requirement_id = requirement["id"]
    note("requirement.create", id=requirement_id)

    analysis = call(client, "POST", f"/requirements/{requirement_id}/analyze", json={})
    data = analysis.get("analysis", {})
    note("requirement.analyze", features=len(data.get("features", [])), clarifications=len(data.get("clarifications", [])))

    plan = call(client, "POST", f"/requirements/{requirement_id}/plan", json={"create_plan": True})
    note("requirement.plan", person_days=plan.get("plan", {}).get("person_days"))

    cases = call(
        client,
        "POST",
        "/skills/case.generate/run",
        json={"requirement_id": requirement_id, "max_cases": 4},
    )
    note("case.generate", generated=len(cases.get("result", {}).get("cases", [])))

    existing_kb = [item for item in call(client, "GET", f"/knowledge-bases?project_id={project_id}") if item["name"] == "验收知识库"]
    if existing_kb:
        kb_id = existing_kb[0]["id"]
        note("knowledge.reuse", kb_id=kb_id)
    else:
        kb = call(client, "POST", "/knowledge-bases", json={"project_id": project_id, "name": "验收知识库"})
        kb_id = kb["id"]
        note("knowledge.create", kb_id=kb_id)
    call(
        client,
        "POST",
        f"/knowledge-bases/{kb_id}/documents/text",
        json={"filename": "导出接口约定.md", "text": "导出接口 GET /api/tickets/export 返回 CSV，超过 5000 条转后台任务，UTF-8 BOM。"},
    )
    hits = call(client, "POST", f"/knowledge-bases/{kb_id}/search", json={"query": "超过 5000 条怎么处理", "top_k": 3})
    note("knowledge.search", kb_id=kb_id, hits=len(hits.get("hits", [])), took_ms=hits.get("took_ms"))

    existing_asset = [item for item in call(client, "GET", f"/api-assets?project_id={project_id}") if item["name"] == "验收演示 API"]
    if existing_asset:
        note("api.reuse", asset_id=existing_asset[0]["id"], endpoints=existing_asset[0]["endpoint_count"])
    else:
        asset = call(client, "POST", "/api-assets/import", json={"project_id": project_id, "spec": json.dumps(SPEC)})
        note("api.import", asset_id=asset["id"], endpoints=asset["endpoint_count"])

    endpoints = call(client, "GET", f"/api-endpoints?project_id={project_id}")
    summary_endpoint = next(item for item in endpoints if item["path"] == "/api/platform/summary")
    debug = call(
        client,
        "POST",
        f"/api-endpoints/{summary_endpoint['id']}/debug",
        json={"base_url": "http://127.0.0.1:8000", "params": {}, "headers": {}},
    )
    note("api.debug", status_code=debug["response"]["status_code"])

    api_cases = call(
        client,
        "POST",
        "/api-cases/generate",
        json={"endpoint_id": summary_endpoint["id"], "count": 2},
    )
    note("api.case.generate", generated=len(api_cases.get("cases", [])))

    if api_cases.get("cases"):
        run = call(client, "POST", f"/api-cases/{api_cases['cases'][0]['id']}/run")
        note("api.case.run", status=run.get("status"), status_code=run.get("status_code"))

    explore = call(
        client,
        "POST",
        "/ui-explore",
        json={
            "project_id": project_id,
            "url": "http://127.0.0.1:8000/ui/#/projects",
            "goal": "打开项目管理页，确认页面出现「项目管理」标题",
            "save": True,
        },
    )
    note("ui.explore", steps=len(explore.get("steps", [])))

    ui_case = explore.get("case") or {}
    if ui_case.get("id"):
        ui_run = call(client, "POST", f"/ui-cases/{ui_case['id']}/run", json={"headless": True})
        note("ui.case.run", status=ui_run.get("status"), ms=ui_run.get("duration_ms"))

    summary = call(client, "GET", "/summary")
    payload = {
        "project_id": project_id,
        "requirement_id": requirement_id,
        "kb_id": kb_id,
        "elapsed_s": round(time.time() - started, 1),
        "platform_summary": summary,
        "steps": steps,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", OUT)
    print("elapsed", payload["elapsed_s"], "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
