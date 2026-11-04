import json
from uuid import uuid4

from fastapi.testclient import TestClient

from app import case_executor
from app.main import app

client = TestClient(app)


def _project():
    response = client.post(
        "/api/platform/projects",
        json={"name": f"exec project {uuid4().hex[:8]}", "description": "exec"},
    )
    assert response.status_code == 201
    return response.json()


def _case(project_id, **overrides):
    payload = {
        "project_id": project_id,
        "title": f"case {uuid4().hex[:8]}",
        "module": "api",
        "priority": "medium",
        "steps": "GET /api/tickets",
        "expected": "200",
        "steps_json": json.dumps(
            [{"action": "GET", "target": "/api/tickets", "data": "", "assert": "status=200"}]
        ),
    }
    payload.update(overrides)
    response = client.post("/api/platform/cases", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _plan(project_id):
    response = client.post(
        "/api/platform/plans",
        json={"project_id": project_id, "name": f"plan {uuid4().hex[:8]}"},
    )
    assert response.status_code == 201
    return response.json()


class FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code
        self.text = f"fake {status_code}"


def test_execute_plan_runs_api_case(monkeypatch):
    project = _project()
    case = _case(project["id"])
    plan = _plan(project["id"])

    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url))
        return FakeResponse(200)

    monkeypatch.setattr(case_executor.httpx, "request", fake_request)

    response = client.post(f"/api/platform/plans/{plan['id']}/execute", json={})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "passed"
    assert body["total"] == 1
    assert body["passed"] == 1
    assert body["results"][0]["case_id"] == case["id"]
    assert calls == [("GET", "http://127.0.0.1:8000/api/tickets")]


def test_execute_plan_reports_failure(monkeypatch):
    project = _project()
    _case(project["id"])
    plan = _plan(project["id"])
    monkeypatch.setattr(case_executor.httpx, "request", lambda *args, **kwargs: FakeResponse(500))

    response = client.post(f"/api/platform/plans/{plan['id']}/execute", json={})
    body = response.json()
    assert body["status"] == "failed"
    assert body["failed"] == 1
    assert "期望 200" in body["results"][0]["message"]


def test_non_api_case_is_skipped(monkeypatch):
    project = _project()
    _case(project["id"], module="web", steps_json="[]")
    plan = _plan(project["id"])

    response = client.post(f"/api/platform/plans/{plan['id']}/execute", json={})
    body = response.json()
    assert body["status"] == "skipped"
    assert body["skipped"] == 1
    assert "暂不支持" in body["results"][0]["message"]


def test_execute_requires_approved_cases():
    project = _project()
    plan = _plan(project["id"])

    response = client.post(f"/api/platform/plans/{plan['id']}/execute", json={})
    assert response.status_code == 400


def test_execution_report_renders(monkeypatch):
    project = _project()
    case = _case(project["id"])
    plan = _plan(project["id"])
    monkeypatch.setattr(case_executor.httpx, "request", lambda *args, **kwargs: FakeResponse(200))
    execution = client.post(f"/api/platform/plans/{plan['id']}/execute", json={}).json()

    response = client.get(f"/api/platform/executions/{execution['id']}/report")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert case["title"] in response.text
    assert "通过率" in response.text
    assert "100.0%" in response.text


def test_relative_target_is_enforced(monkeypatch):
    project = _project()
    _case(
        project["id"],
        steps_json=json.dumps(
            [{"action": "GET", "target": "http://example.com/steal", "data": "", "assert": "status=200"}]
        ),
    )
    plan = _plan(project["id"])

    response = client.post(f"/api/platform/plans/{plan['id']}/execute", json={})
    body = response.json()
    assert body["status"] == "failed"
    assert "相对路径" in body["results"][0]["message"]
