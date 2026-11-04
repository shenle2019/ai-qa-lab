from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _project():
    response = client.post(
        "/api/platform/projects",
        json={"name": f"crud project {uuid4().hex[:8]}", "description": "crud"},
    )
    assert response.status_code == 201
    return response.json()


def _case(project_id: int, **overrides):
    payload = {
        "project_id": project_id,
        "title": f"case {uuid4().hex[:8]}",
        "module": "api",
        "priority": "medium",
        "steps": "step",
        "expected": "ok",
    }
    payload.update(overrides)
    response = client.post("/api/platform/cases", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _plan(project_id: int):
    response = client.post(
        "/api/platform/plans",
        json={"project_id": project_id, "name": f"plan {uuid4().hex[:8]}"},
    )
    assert response.status_code == 201
    return response.json()


def test_create_project_and_get():
    project = _project()
    fetched = client.get(f"/api/platform/projects/{project['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == project["name"]


def test_duplicate_project_name_returns_same_id():
    name = f"dup {uuid4().hex[:8]}"
    first = client.post("/api/platform/projects", json={"name": name}).json()
    second = client.post("/api/platform/projects", json={"name": name}).json()
    assert first["id"] == second["id"]


def test_list_projects_contains_project():
    project = _project()
    ids = [item["id"] for item in client.get("/api/platform/projects").json()]
    assert project["id"] in ids


def test_missing_project_returns_404():
    assert client.get("/api/platform/projects/99999999").status_code == 404


def test_create_case_and_list():
    project = _project()
    case = _case(project["id"])
    cases = client.get("/api/platform/cases").json()
    assert any(item["id"] == case["id"] for item in cases)


def test_filter_cases_by_project():
    project = _project()
    case = _case(project["id"])
    cases = client.get(f"/api/platform/cases?project_id={project['id']}").json()
    assert [item["id"] for item in cases] == [case["id"]]


def test_case_invalid_project_404():
    response = client.post(
        "/api/platform/cases",
        json={"project_id": 99999999, "title": "orphan"},
    )
    assert response.status_code == 404


def test_case_high_priority():
    project = _project()
    case = _case(project["id"], priority="high")
    assert case["priority"] == "high"


def test_case_low_priority():
    project = _project()
    case = _case(project["id"], priority="low")
    assert case["priority"] == "low"


def test_case_web_module():
    project = _project()
    case = _case(project["id"], module="web")
    assert case["module"] == "web"


def test_create_plan_and_get():
    project = _project()
    plan = _plan(project["id"])
    fetched = client.get(f"/api/platform/plans/{plan['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "draft"


def test_filter_plans_by_project():
    project = _project()
    plan = _plan(project["id"])
    plans = client.get(f"/api/platform/plans?project_id={project['id']}").json()
    assert [item["id"] for item in plans] == [plan["id"]]


def test_plan_invalid_project_404():
    response = client.post("/api/platform/plans", json={"project_id": 99999999, "name": "orphan"})
    assert response.status_code == 404


def test_missing_plan_returns_404():
    assert client.get("/api/platform/plans/99999999").status_code == 404


def test_run_plan_passed():
    project = _project()
    plan = _plan(project["id"])
    response = client.post(
        f"/api/platform/plans/{plan['id']}/run",
        json={"results": [
            {"case_name": "a", "status": "passed", "duration_ms": 10},
            {"case_name": "b", "status": "passed", "duration_ms": 20},
        ]},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "passed"
    assert payload["passed"] == 2
    assert payload["failed"] == 0


def test_run_plan_failed():
    project = _project()
    plan = _plan(project["id"])
    response = client.post(
        f"/api/platform/plans/{plan['id']}/run",
        json={"results": [
            {"case_name": "a", "status": "passed", "duration_ms": 10},
            {"case_name": "b", "status": "failed", "duration_ms": 20, "message": "boom"},
        ]},
    )
    assert response.json()["status"] == "failed"
    assert response.json()["failed"] == 1


def test_run_missing_plan_404():
    response = client.post("/api/platform/plans/99999999/run", json={"results": []})
    assert response.status_code == 404


def test_list_executions_contains_run():
    project = _project()
    plan = _plan(project["id"])
    execution = client.post(
        f"/api/platform/plans/{plan['id']}/run",
        json={"results": [{"case_name": "a", "status": "passed", "duration_ms": 10}]},
    ).json()
    ids = [item["id"] for item in client.get("/api/platform/executions").json()]
    assert execution["id"] in ids


def test_get_execution_results():
    project = _project()
    plan = _plan(project["id"])
    execution = client.post(
        f"/api/platform/plans/{plan['id']}/run",
        json={"results": [{"case_name": "a", "status": "passed", "duration_ms": 10}]},
    ).json()
    fetched = client.get(f"/api/platform/executions/{execution['id']}").json()
    assert len(fetched["results"]) == 1
    assert fetched["results"][0]["status"] == "passed"


def test_missing_execution_404():
    assert client.get("/api/platform/executions/99999999").status_code == 404


def test_create_defect_and_patch():
    project = _project()
    defect = client.post(
        "/api/platform/defects",
        json={"project_id": project["id"], "title": "bug", "severity": "high"},
    ).json()
    patched = client.patch(f"/api/platform/defects/{defect['id']}", json={"status": "fixed"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "fixed"


def test_filter_defects_by_project():
    project = _project()
    defect = client.post(
        "/api/platform/defects",
        json={"project_id": project["id"], "title": "bug"},
    ).json()
    defects = client.get(f"/api/platform/defects?project_id={project['id']}").json()
    assert [item["id"] for item in defects] == [defect["id"]]


def test_invalid_defect_status_422():
    project = _project()
    defect = client.post(
        "/api/platform/defects",
        json={"project_id": project["id"], "title": "bug"},
    ).json()
    response = client.patch(f"/api/platform/defects/{defect['id']}", json={"status": "nope"})
    assert response.status_code == 422


def test_patch_missing_defect_404():
    assert client.patch("/api/platform/defects/99999999", json={"status": "closed"}).status_code == 404


def test_import_minipytest_report():
    report = {
        "started_at": "2026-11-03T18:00:00",
        "tests": [
            {"id": "a", "name": "pass", "status": "passed", "duration_ms": 10},
            {"id": "b", "name": "fail", "status": "failed", "duration_ms": 20, "failure": {"message": "boom"}},
        ],
    }
    response = client.post("/api/platform/import/minipytest", json={"report": report})
    assert response.status_code == 201
    assert response.json()["total"] == 2
    assert response.json()["failed"] == 1


def test_summary_shape():
    payload = client.get("/api/platform/summary").json()
    for key in ("projects", "cases", "plans", "executions", "defects", "open_defects", "pass_rate"):
        assert key in payload
