from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _project(name: str | None = None) -> dict:
    response = client.post(
        "/api/platform/projects",
        json={"name": name or f"platform {uuid4().hex[:8]}", "description": "test"},
    )
    assert response.status_code == 201
    return response.json()


def test_summary_shape():
    response = client.get("/api/platform/summary")
    assert response.status_code == 200
    payload = response.json()
    for key in ("projects", "cases", "plans", "executions", "defects", "open_defects", "pass_rate"):
        assert key in payload


def test_create_project_case_plan():
    project = _project()
    case = client.post(
        "/api/platform/cases",
        json={
            "project_id": project["id"],
            "title": "API smoke",
            "module": "api",
            "priority": "high",
            "steps": "GET /health",
            "expected": "200",
        },
    ).json()
    plan = client.post(
        "/api/platform/plans",
        json={"project_id": project["id"], "name": "regression"},
    ).json()
    assert case["project_id"] == project["id"]
    assert plan["status"] == "draft"
    assert client.get(f"/api/platform/projects/{project['id']}").json()["name"] == project["name"]


def test_run_plan_creates_execution():
    project = _project()
    plan = client.post(
        "/api/platform/plans",
        json={"project_id": project["id"], "name": "run me"},
    ).json()
    response = client.post(
        f"/api/platform/plans/{plan['id']}/run",
        json={
            "results": [
                {"case_name": "a", "status": "passed", "duration_ms": 10},
                {"case_name": "b", "status": "passed", "duration_ms": 20},
                {"case_name": "c", "status": "failed", "duration_ms": 30, "message": "boom"},
            ]
        },
    )
    assert response.status_code == 201
    execution = response.json()
    assert execution["total"] == 3
    assert execution["passed"] == 2
    assert execution["failed"] == 1
    assert execution["status"] == "failed"
    assert len(execution["results"]) == 3


def test_import_minipytest_report():
    report = {
        "started_at": "2026-11-03T17:00:00",
        "tests": [
            {"id": "a", "name": "pass", "status": "passed", "duration_ms": 10},
            {"id": "b", "name": "fail", "status": "failed", "duration_ms": 20, "failure": {"message": "boom"}},
            {"id": "c", "name": "skip", "status": "skipped", "duration_ms": 0},
        ],
    }
    response = client.post("/api/platform/import/minipytest", json={"report": report})
    assert response.status_code == 201
    execution = response.json()
    assert execution["total"] == 3
    assert execution["failed"] == 1
    assert execution["skipped"] == 1


def test_defect_lifecycle():
    project = _project()
    defect = client.post(
        "/api/platform/defects",
        json={"project_id": project["id"], "title": "broken page", "severity": "high"},
    ).json()
    closed = client.patch(f"/api/platform/defects/{defect['id']}", json={"status": "closed"})
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"


def test_seed_is_idempotent():
    first = client.post("/api/platform/seed")
    second = client.post("/api/platform/seed")
    assert first.status_code == 200
    assert second.status_code == 200
    projects = client.get("/api/platform/projects").json()
    assert sum(1 for item in projects if item["name"] == "AI 质量平台演示") == 1
