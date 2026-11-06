"""UI automation: case CRUD, step validation, execution, explore and chat."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ui_steps import StepError, normalise_steps, parse_env

client = TestClient(app)

STEPS = [
    {"action": "goto", "value": "http://127.0.0.1:8000/ui/#/projects"},
    {"action": "assert_text", "target": "body", "value": "项目管理"},
]

SNAPSHOT = {
    "title": "AI 测试平台",
    "url": "http://127.0.0.1:8000/ui/#/projects",
    "text": "项目管理 新建项目",
    "nodes": [
        {"tag": "a", "text": "项目管理", "name": "", "id": "", "placeholder": "", "href": "#/projects"},
        {"tag": "button", "text": "新建项目", "name": "", "id": "", "placeholder": "", "href": ""},
    ],
}


@pytest.fixture()
def project_id() -> int:
    name = f"UI 自动化项目-{uuid.uuid4().hex[:6]}"
    response = client.post("/api/platform/projects", json={"name": name, "description": "ui"})
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


@pytest.fixture()
def llm_ready() -> None:
    models = client.get("/api/platform/models").json()
    if not models:
        client.post(
            "/api/platform/models",
            json={
                "name": "fake",
                "provider": "deepseek",
                "base_url": "https://api.deepseek.com",
                "model_name": "deepseek-chat",
            },
        )


def _create_case(project_id: int, **overrides) -> dict:
    payload = {
        "project_id": project_id,
        "title": "打开项目管理页并校验标题",
        "module": "UI 冒烟",
        "base_url": "http://127.0.0.1:8000",
        "env": {"token": "abc"},
        "steps": STEPS,
        "status": "ready",
    }
    payload.update(overrides)
    response = client.post("/api/platform/ui-cases", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_case_crud(project_id: int) -> None:
    case = _create_case(project_id)
    assert case["source"] == "manual"
    assert len(case["steps"]) == 2
    assert case["env"] == {"token": "abc"}

    listed = client.get("/api/platform/ui-cases", params={"project_id": project_id})
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [case["id"]]

    detail = client.get(f"/api/platform/ui-cases/{case['id']}")
    assert detail.status_code == 200
    assert detail.json()["title"] == case["title"]

    patched = client.patch(f"/api/platform/ui-cases/{case['id']}", json={"title": "改名后的用例", "status": "draft"})
    assert patched.status_code == 200
    assert patched.json()["title"] == "改名后的用例"
    assert patched.json()["status"] == "draft"

    deleted = client.delete(f"/api/platform/ui-cases/{case['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/platform/ui-cases/{case['id']}").status_code == 404


def test_case_rejects_bad_step(project_id: int) -> None:
    response = client.post(
        "/api/platform/ui-cases",
        json={"project_id": project_id, "title": "坏步骤", "steps": [{"action": "jump", "target": "body"}]},
    )
    assert response.status_code == 400
    assert "action" in response.json()["detail"]


def test_case_rejects_bad_status(project_id: int) -> None:
    response = client.post(
        "/api/platform/ui-cases",
        json={"project_id": project_id, "title": "坏状态", "steps": STEPS, "status": "weird"},
    )
    assert response.status_code == 400


def test_script_export(project_id: int) -> None:
    case = _create_case(project_id)
    response = client.get(f"/api/platform/ui-cases/{case['id']}/script")
    assert response.status_code == 200
    body = response.json()
    assert "from playwright.sync_api import sync_playwright" in body["script"]
    assert "goto" in body["script"]
    assert "localStorage.setItem" in body["script"]


def test_run_records_result(project_id: int, monkeypatch: pytest.MonkeyPatch) -> None:
    case = _create_case(project_id)

    def fake_execute(case_obj, *, run_id=None, headless=True):
        return {
            "steps": [
                {"index": 0, "action": "goto", "target": None, "value": "http://x", "ok": True, "error": None},
            ],
            "error": None,
            "screenshot": None,
            "duration_ms": 42,
        }

    monkeypatch.setattr("app.skills.builtin.ui_run.execute_case", fake_execute)
    response = client.post(f"/api/platform/ui-cases/{case['id']}/run")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "passed"
    assert body["duration_ms"] == 42
    assert body["run_id"]

    runs = client.get("/api/platform/ui-runs", params={"project_id": project_id}).json()
    assert len(runs) == 1
    assert runs[0]["status"] == "passed"
    detail = client.get(f"/api/platform/ui-runs/{body['run_id']}").json()
    assert detail["case_id"] == case["id"]


def test_run_records_failure(project_id: int, monkeypatch: pytest.MonkeyPatch) -> None:
    case = _create_case(project_id)

    def fake_execute(case_obj, *, run_id=None, headless=True):
        return {
            "steps": [
                {"index": 0, "action": "goto", "target": None, "value": "http://x", "ok": False, "error": "超时"},
            ],
            "error": "第 1 步失败：超时",
            "screenshot": f"ui-run-{run_id}.png",
            "duration_ms": 10,
        }

    monkeypatch.setattr("app.skills.builtin.ui_run.execute_case", fake_execute)
    body = client.post(f"/api/platform/ui-cases/{case['id']}/run").json()
    assert body["status"] == "failed"
    assert body["screenshot"] == f"ui-run-{body['run_id']}.png"


def test_run_missing_case() -> None:
    assert client.post("/api/platform/ui-cases/999999/run").status_code == 404


def test_explore_saves_draft(project_id: int, llm_ready: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.skills.builtin.ui_case_generate.snapshot", lambda url, **kwargs: SNAPSHOT)
    monkeypatch.setattr(
        "app.llm_client.chat_json",
        lambda *args, **kwargs: {"reasoning": "先看标题", "steps": STEPS},
    )
    response = client.post(
        "/api/platform/ui-explore",
        json={
            "project_id": project_id,
            "url": "http://127.0.0.1:8000/ui/#/projects",
            "goal": "确认页面有项目管理标题",
            "save": True,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "AI 测试平台"
    assert len(body["steps"]) == 2
    assert body["case"]["source"] == "ai"
    assert body["case"]["module"] == "AI 探索"
    assert body["case"]["status"] == "draft"


def test_explore_rejects_empty_goal(project_id: int) -> None:
    response = client.post(
        "/api/platform/ui-explore",
        json={"project_id": project_id, "url": "http://127.0.0.1:8000/ui/", "goal": ""},
    )
    assert response.status_code == 422


def test_chat_returns_reply(project_id: int, llm_ready: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.skills.builtin.ui_run.snapshot", lambda url, **kwargs: SNAPSHOT)
    monkeypatch.setattr("app.llm_client.chat_text", lambda *args, **kwargs: "页面左侧是导航，右侧是项目列表。")
    response = client.post(
        "/api/platform/ui-chat",
        json={"url": "http://127.0.0.1:8000/ui/#/projects", "question": "这个页面有什么？"},
    )
    assert response.status_code == 200, response.text
    assert "导航" in response.json()["reply"]


def test_step_helpers() -> None:
    assert len(normalise_steps(STEPS)) == 2
    assert normalise_steps("[]") == []
    with pytest.raises(StepError):
        normalise_steps([{"action": "unknown"}])
    with pytest.raises(StepError):
        normalise_steps([{"action": "click"}])
    env = parse_env('{"a": 1, "b": true}')
    assert env == {"a": "1", "b": "True"}
