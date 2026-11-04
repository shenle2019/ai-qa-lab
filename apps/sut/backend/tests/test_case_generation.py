import json
from uuid import uuid4

from fastapi.testclient import TestClient

from app import case_generator
from app.main import app

client = TestClient(app)


def _project():
    response = client.post(
        "/api/platform/projects",
        json={"name": f"gen project {uuid4().hex[:8]}", "description": "gen"},
    )
    assert response.status_code == 201
    return response.json()


def _model(**overrides):
    payload = {
        "name": f"gen model {uuid4().hex[:8]}",
        "base_url": "https://api.deepseek.com",
        "model_name": "deepseek-chat",
        "api_key": "sk-test",
    }
    payload.update(overrides)
    response = client.post("/api/platform/models", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _fake_generation(monkeypatch):
    def fake_chat_json(*args, **kwargs):
        return {
            "cases": [
                {
                    "title": "登录成功返回 200",
                    "module": "api",
                    "priority": "high",
                    "steps": [
                        {"action": "POST", "target": "/login", "data": "valid", "assert": "200"}
                    ],
                    "expected": "返回 200 和 token",
                },
                {
                    "title": "错误密码返回 401",
                    "module": "api",
                    "priority": "medium",
                    "steps": [
                        {"action": "POST", "target": "/login", "data": "wrong", "assert": "401"}
                    ],
                    "expected": "返回 401",
                },
                {
                    "title": "登录成功返回 200",
                    "module": "api",
                    "priority": "high",
                    "steps": [{"action": "dup"}],
                    "expected": "重复标题应被丢弃",
                },
            ]
        }

    monkeypatch.setattr(case_generator.llm_client, "chat_json", fake_chat_json)


def test_generate_cases_creates_drafts(monkeypatch):
    project = _project()
    model = _model()
    _fake_generation(monkeypatch)

    response = client.post(
        "/api/platform/generate-cases",
        json={
            "project_id": project["id"],
            "requirement": "实现登录接口，校验用户名密码，失败返回 401",
            "model_id": model["id"],
            "max_cases": 5,
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["model_name"] == "deepseek-chat"
    assert body["prompt_version"] == case_generator.PROMPT_VERSION
    assert len(body["cases"]) == 2
    for case in body["cases"]:
        assert case["status"] == "draft"
        assert case["source"] == "ai"
        assert case["prompt_version"] == case_generator.PROMPT_VERSION
        assert json.loads(case["steps_json"])


def test_review_gate_flow(monkeypatch):
    project = _project()
    model = _model()
    _fake_generation(monkeypatch)
    generated = client.post(
        "/api/platform/generate-cases",
        json={
            "project_id": project["id"],
            "requirement": "实现登录接口，校验用户名密码，失败返回 401",
            "model_id": model["id"],
            "max_cases": 1,
        },
    ).json()
    case = generated["cases"][0]

    submitted = client.post(f"/api/platform/cases/{case['id']}/submit-review")
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "pending_review"

    reviewed = client.post(
        f"/api/platform/cases/{case['id']}/review",
        json={"decision": "approved", "reviewer": "tester", "comment": "ok"},
    )
    assert reviewed.status_code == 201
    assert reviewed.json()["decision"] == "approved"

    listed = client.get(f"/api/platform/cases?project_id={project['id']}").json()
    assert listed[0]["status"] == "approved"

    again = client.post(
        f"/api/platform/cases/{case['id']}/review",
        json={"decision": "rejected"},
    )
    assert again.status_code == 409

    history = client.get(f"/api/platform/cases/{case['id']}/reviews").json()
    assert history[0]["reviewer"] == "tester"


def test_rejected_case_cannot_run(monkeypatch):
    project = _project()
    model = _model()
    _fake_generation(monkeypatch)
    case = client.post(
        "/api/platform/generate-cases",
        json={
            "project_id": project["id"],
            "requirement": "实现登录接口，校验用户名密码，失败返回 401",
            "model_id": model["id"],
            "max_cases": 1,
        },
    ).json()["cases"][0]
    client.post(f"/api/platform/cases/{case['id']}/submit-review")
    client.post(
        f"/api/platform/cases/{case['id']}/review",
        json={"decision": "rejected", "comment": "预期不清楚"},
    )

    plan = client.post(
        "/api/platform/plans",
        json={"project_id": project["id"], "name": f"plan {uuid4().hex[:6]}"},
    ).json()
    blocked = client.post(
        f"/api/platform/plans/{plan['id']}/run",
        json={
            "results": [
                {"case_id": case["id"], "case_name": case["title"], "status": "passed"}
            ]
        },
    )
    assert blocked.status_code == 409


def test_generate_cases_requires_existing_model():
    project = _project()
    response = client.post(
        "/api/platform/generate-cases",
        json={
            "project_id": project["id"],
            "requirement": "实现登录接口，校验用户名密码，失败返回 401",
            "model_id": 999999,
        },
    )
    assert response.status_code == 404
