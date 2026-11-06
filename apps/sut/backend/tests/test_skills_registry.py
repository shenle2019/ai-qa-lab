"""Tests for the pluggable skill registry (Phase 0)."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_skills_returns_builtins():
    response = client.get("/api/platform/skills")
    assert response.status_code == 200
    items = response.json()
    ids = {item["id"] for item in items}
    assert {"case.generate", "case.list", "project.list"} <= ids
    for item in items:
        assert item["name"]
        assert item["category"]
        assert isinstance(item["input_schema"], dict)
        assert item["enabled"] is True


def test_list_skills_filters_by_category():
    response = client.get("/api/platform/skills?category=case")
    assert response.status_code == 200
    items = response.json()
    assert items
    assert all(item["category"] == "case" for item in items)


def test_get_skill_descriptor():
    response = client.get("/api/platform/skills/case.generate")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "case.generate"
    assert body["category"] == "case"
    assert "requirement" in body["input_schema"]["properties"]


def test_get_missing_skill_returns_404():
    assert client.get("/api/platform/skills/nope.nope").status_code == 404


def test_run_unknown_skill_returns_404():
    response = client.post("/api/platform/skills/nope.nope/run", json={})
    assert response.status_code == 404


def test_run_project_list_skill():
    response = client.post("/api/platform/skills/project.list/run", json={})
    assert response.status_code == 200
    result = response.json()["result"]
    assert "projects" in result
    assert isinstance(result["total"], int)


def test_run_case_list_skill_filters_by_project():
    project = client.post(
        "/api/platform/projects",
        json={"name": f"skill project {uuid4().hex[:8]}"},
    ).json()
    client.post(
        "/api/platform/cases",
        json={
            "project_id": project["id"],
            "title": "skill case",
            "module": "api",
            "priority": "medium",
            "steps": "step",
            "expected": "ok",
        },
    )
    response = client.post(
        "/api/platform/skills/case.list/run",
        json={"project_id": project["id"]},
    )
    assert response.status_code == 200
    cases = response.json()["result"]["cases"]
    assert [c["title"] for c in cases] == ["skill case"]


def test_run_case_generate_requires_requirement():
    project = client.post(
        "/api/platform/projects",
        json={"name": f"skill project {uuid4().hex[:8]}"},
    ).json()
    response = client.post(
        "/api/platform/skills/case.generate/run",
        json={"project_id": project["id"]},
    )
    assert response.status_code == 400
    assert "requirement" in response.json()["detail"]
