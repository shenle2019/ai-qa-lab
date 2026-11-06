"""Phase 2: case management — edit, delete, batch review flow, generation from analysis."""

import json
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _project():
    response = client.post(
        "/api/platform/projects",
        json={"name": f"case mgmt {uuid4().hex[:8]}", "description": "phase2"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _model():
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/platform/models",
        json={
            "name": f"model {suffix}",
            "provider": "deepseek",
            "base_url": "https://api.deepseek.com",
            "model_name": f"deepseek-chat-{suffix}",
            "api_key": "sk-test-1234567890",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _case(project_id: int, **overrides):
    payload = {
        "project_id": project_id,
        "title": f"case {uuid4().hex[:8]}",
        "module": "api",
        "priority": "medium",
        "steps": "打开页面\n点击按钮",
        "expected": "接口返回 200",
    }
    payload.update(overrides)
    response = client.post("/api/platform/cases", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _batch(**payload):
    response = client.post("/api/platform/cases/batch", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_patch_case_updates_fields():
    project = _project()
    case = _case(project["id"])

    response = client.patch(
        f"/api/platform/cases/{case['id']}",
        json={"title": "改过的标题", "priority": "high", "expected": "返回 201"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "改过的标题"
    assert body["priority"] == "high"
    assert body["expected"] == "返回 201"
    assert body["status"] == case["status"]
    assert body["module"] == case["module"]


def test_patch_case_rejects_bad_payload():
    project = _project()
    case = _case(project["id"])

    assert client.patch(f"/api/platform/cases/{case['id']}", json={}).status_code == 400
    assert client.patch(f"/api/platform/cases/{case['id']}", json={"priority": "urgent"}).status_code == 400
    assert client.patch(f"/api/platform/cases/{case['id']}", json={"title": "   "}).status_code == 400
    assert client.patch("/api/platform/cases/999999", json={"title": "x"}).status_code == 404


def test_get_and_delete_case():
    project = _project()
    case = _case(project["id"])

    detail = client.get(f"/api/platform/cases/{case['id']}")
    assert detail.status_code == 200
    assert detail.json()["title"] == case["title"]

    assert client.delete(f"/api/platform/cases/{case['id']}").status_code == 204
    assert client.get(f"/api/platform/cases/{case['id']}").status_code == 404
    assert client.delete(f"/api/platform/cases/{case['id']}").status_code == 404


def test_batch_review_flow():
    project = _project()
    first = _case(project["id"])
    second = _case(project["id"])

    reset = _batch(action="draft", ids=[first["id"], second["id"]])
    assert reset["updated"] == 2
    assert client.get(f"/api/platform/cases/{first['id']}").json()["status"] == "draft"

    submitted = _batch(action="submit_review", ids=[first["id"], second["id"]])
    assert submitted["updated"] == 2

    approved = _batch(action="approve", ids=[first["id"]], reviewer="qa", comment="ok")
    assert approved["updated"] == 1

    detail = client.get(f"/api/platform/cases/{first['id']}").json()
    assert detail["status"] == "approved"
    reviews = client.get(f"/api/platform/cases/{first['id']}/reviews").json()
    assert reviews and reviews[0]["decision"] == "approved"
    assert reviews[0]["comment"] == "ok"
    assert reviews[0]["reviewer"] == "qa"


def test_batch_skips_cases_in_wrong_status():
    project = _project()
    case = _case(project["id"])

    # Fresh cases default to approved, so approving again must be skipped.
    body = _batch(action="approve", ids=[case["id"], 999999])
    assert body["updated"] == 0
    assert len(body["skipped"]) == 2
    reasons = " ".join(item["reason"] for item in body["skipped"])
    assert "approved" in reasons
    assert "用例不存在" in reasons


def test_batch_delete_and_validation():
    project = _project()
    case = _case(project["id"])

    removed = _batch(action="delete", ids=[case["id"]])
    assert removed["updated"] == 1
    assert client.get(f"/api/platform/cases/{case['id']}").status_code == 404

    assert client.post("/api/platform/cases/batch", json={"action": "explode", "ids": [1]}).status_code == 400
    assert client.post("/api/platform/cases/batch", json={"action": "delete", "ids": []}).status_code == 400


def test_generate_cases_from_requirement_analysis(monkeypatch):
    project = _project()
    _model()
    requirement = client.post(
        "/api/platform/requirements",
        json={
            "project_id": project["id"],
            "title": "导出功能",
            "body": "列表页增加导出 CSV 按钮，超过 5000 条转后台任务。",
        },
    )
    assert requirement.status_code == 201, requirement.text
    rid = requirement.json()["id"]

    analysis = {
        "summary": "增加 CSV 导出",
        "features": [
            {"name": "导出按钮", "description": "列表页顶部", "priority": "high", "acceptance": "点击后下载"},
            {"name": "大结果集后台导出", "description": "超过 5000 条", "priority": "high", "acceptance": "站内信通知"},
        ],
        "ui": [],
        "clarifications": [],
        "risks": [],
    }

    captured = {}

    def fake_chat_json(db, config, messages, **kwargs):
        if kwargs.get("purpose") == "requirement_analysis":
            return analysis
        captured["messages"] = json.dumps(messages, ensure_ascii=False)
        return {
            "cases": [
                {
                    "title": "导出接口返回 200",
                    "module": "api",
                    "priority": "high",
                    "steps": [
                        {"action": "GET", "target": "/api/tickets/export", "data": "", "assert": "status=200"}
                    ],
                    "expected": "返回 CSV 流",
                }
            ]
        }

    monkeypatch.setattr("app.llm_client.chat_json", fake_chat_json)

    assert client.post(f"/api/platform/requirements/{rid}/analyze").status_code == 200

    generated = client.post(
        "/api/platform/skills/case.generate/run",
        json={"project_id": project["id"], "requirement_id": rid, "max_cases": 3},
    )
    assert generated.status_code == 200, generated.text
    body = generated.json()["result"]
    assert len(body["cases"]) == 1
    assert body["cases"][0]["status"] == "draft"
    assert body["cases"][0]["steps"]

    prompt = captured.get("messages", "")
    assert "导出按钮" in prompt
    assert "大结果集后台导出" in prompt
    assert "已识别的功能点" in prompt


def test_case_skills_are_registered():
    response = client.get("/api/platform/skills", params={"category": "case"})
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert {"case.generate", "case.list", "case.update", "case.batch"} <= ids
