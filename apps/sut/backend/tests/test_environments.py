from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _project() -> int:
    response = client.post(
        "/api/platform/projects",
        json={"name": "环境测试项目", "description": "env cases"},
    )
    assert response.status_code in (200, 201)
    return response.json()["id"]


def test_list_is_empty_for_new_project():
    project_id = _project()
    response = client.get(f"/api/platform/environments?project_id={project_id}")
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_list():
    project_id = _project()
    response = client.post(
        "/api/platform/environments",
        json={
            "project_id": project_id,
            "name": "测试环境",
            "kind": "test",
            "base_url": "http://127.0.0.1:8000",
            "variables": {"token": "abc"},
            "note": "本地",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "测试环境"
    assert body["variables"] == {"token": "abc"}

    listed = client.get(f"/api/platform/environments?project_id={project_id}").json()
    assert [item["id"] for item in listed] == [body["id"]]


def test_rejects_duplicate_name():
    project_id = _project()
    payload = {"project_id": project_id, "name": "预发", "kind": "staging"}
    assert client.post("/api/platform/environments", json=payload).status_code == 201
    again = client.post("/api/platform/environments", json=payload)
    assert again.status_code == 409


def test_rejects_bad_kind_and_blank_name():
    project_id = _project()
    bad_kind = client.post(
        "/api/platform/environments",
        json={"project_id": project_id, "name": "x", "kind": "uat"},
    )
    assert bad_kind.status_code == 400

    blank = client.post(
        "/api/platform/environments",
        json={"project_id": project_id, "name": "   ", "kind": "test"},
    )
    assert blank.status_code in (400, 422)


def test_update_and_delete():
    project_id = _project()
    created = client.post(
        "/api/platform/environments",
        json={"project_id": project_id, "name": "旧名字", "kind": "test"},
    ).json()

    patched = client.patch(
        f"/api/platform/environments/{created['id']}",
        json={"name": "新名字", "base_url": "https://example.com", "variables": {"a": "1"}},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "新名字"
    assert patched.json()["base_url"] == "https://example.com"
    assert patched.json()["variables"] == {"a": "1"}

    assert client.delete(f"/api/platform/environments/{created['id']}").status_code == 204
    assert client.delete(f"/api/platform/environments/{created['id']}").status_code == 404


def test_summary_exposes_result_counts():
    body = client.get("/api/platform/summary").json()
    for key in ("results_passed", "results_failed", "results_total"):
        assert key in body
        assert isinstance(body[key], int)


def test_health_reports_docs_flag():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert isinstance(body["docs"], bool)
