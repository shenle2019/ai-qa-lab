import json
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _project():
    response = client.post(
        "/api/platform/projects",
        json={"name": f"req project {uuid4().hex[:8]}", "description": "req"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _model():
    response = client.post(
        "/api/platform/models",
        json={
            "name": f"req model {uuid4().hex[:8]}",
            "base_url": "https://api.deepseek.com",
            "model_name": "deepseek-chat",
            "api_key": "sk-test",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _requirement(project_id, **overrides):
    payload = {
        "project_id": project_id,
        "title": f"需求 {uuid4().hex[:6]}",
        "body": "支持按状态筛选工单，并导出 CSV。",
        "priority": "high",
    }
    payload.update(overrides)
    response = client.post("/api/platform/requirements", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


ANALYSIS = {
    "summary": "工单列表增加状态筛选和 CSV 导出。",
    "features": [
        {
            "name": "状态筛选",
            "description": "按工单状态过滤列表",
            "priority": "high",
            "acceptance": "选择状态后列表只显示该状态的工单",
        }
    ],
    "ui": [{"page": "工单列表", "description": "顶部筛选栏", "elements": ["状态下拉框"]}],
    "clarifications": [{"question": "导出是否包含已关闭工单？", "why": "影响数据量"}],
    "risks": ["大数据量导出超时"],
}

PLAN = {
    "goal": "验证筛选与导出功能正确",
    "scope_in": ["状态筛选", "CSV 导出"],
    "scope_out": ["权限模型改造"],
    "approach": "接口优先，再补前端联调",
    "person_days": 2.5,
    "milestones": [
        {"name": "接口测试", "days": 1, "deliverable": "接口用例与报告"},
        {"name": "回归", "days": 1.5, "deliverable": "回归结论"},
    ],
    "environments": ["测试环境"],
    "test_data": ["100 条不同状态工单"],
    "risks": ["导出接口耗时不稳定"],
}


def _fake_llm(monkeypatch):
    def fake_chat_json(*args, **kwargs):
        if kwargs.get("purpose") == "requirement_plan":
            return PLAN
        return ANALYSIS

    monkeypatch.setattr("app.llm_client.chat_json", fake_chat_json)


def test_create_and_list_requirement():
    project = _project()
    created = _requirement(project["id"])
    assert created["status"] == "draft"
    assert created["analysis"] is None
    assert created["attachments"] == []

    listed = client.get(f"/api/platform/requirements?project_id={project['id']}").json()
    assert any(item["id"] == created["id"] for item in listed)

    fetched = client.get(f"/api/platform/requirements/{created['id']}").json()
    assert fetched["title"] == created["title"]
    assert fetched["messages"] == []


def test_create_requirement_validates_input():
    project = _project()
    bad_status = client.post(
        "/api/platform/requirements",
        json={"project_id": project["id"], "title": "x", "status": "done"},
    )
    assert bad_status.status_code == 400

    bad_project = client.post(
        "/api/platform/requirements",
        json={"project_id": 999999, "title": "x"},
    )
    assert bad_project.status_code == 404

    missing = client.get("/api/platform/requirements/999999")
    assert missing.status_code == 404


def test_update_and_delete_requirement():
    project = _project()
    created = _requirement(project["id"])

    patched = client.patch(
        f"/api/platform/requirements/{created['id']}",
        json={"title": "改过的标题", "priority": "urgent"},
    )
    assert patched.status_code == 200
    assert patched.json()["title"] == "改过的标题"
    assert patched.json()["priority"] == "urgent"

    deleted = client.delete(f"/api/platform/requirements/{created['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/platform/requirements/{created['id']}").status_code == 404


def test_upload_text_attachment_extracts_text():
    project = _project()
    req = _requirement(project["id"])

    response = client.post(
        f"/api/platform/requirements/{req['id']}/attachments",
        files={"file": ("spec.md", "# 需求\n支持导出 CSV。".encode("utf-8"), "text/markdown")},
    )
    assert response.status_code == 201, response.text
    attachment = response.json()
    assert attachment["filename"] == "spec.md"
    assert attachment["chars"] > 0
    assert attachment["extract_note"] == ""

    detail = client.get(f"/api/platform/requirements/{req['id']}").json()
    assert detail["source_filename"] == "spec.md"
    assert len(detail["attachments"]) == 1

    download = client.get(
        f"/api/platform/requirements/{req['id']}/attachments/{attachment['id']}/download"
    )
    assert download.status_code == 200
    assert "导出 CSV" in download.content.decode("utf-8")

    removed = client.delete(
        f"/api/platform/requirements/{req['id']}/attachments/{attachment['id']}"
    )
    assert removed.status_code == 204
    assert client.get(f"/api/platform/requirements/{req['id']}").json()["attachments"] == []


def test_upload_unknown_type_keeps_note():
    project = _project()
    req = _requirement(project["id"])
    response = client.post(
        f"/api/platform/requirements/{req['id']}/attachments",
        files={"file": ("mock.bin", b"\x00\x01\x02", "application/octet-stream")},
    )
    assert response.status_code == 201
    assert response.json()["extract_note"]
    assert response.json()["chars"] == 0


def test_analyze_requirement_saves_analysis(monkeypatch):
    project = _project()
    _model()
    req = _requirement(project["id"])
    _fake_llm(monkeypatch)

    response = client.post(f"/api/platform/requirements/{req['id']}/analyze")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["analysis"]["features"][0]["name"] == "状态筛选"
    assert body["requirement"]["status"] == "analyzed"

    detail = client.get(f"/api/platform/requirements/{req['id']}").json()
    assert detail["analysis"]["clarifications"][0]["question"].startswith("导出")
    assert json.loads(json.dumps(detail["analysis"]))["summary"]


def test_plan_requires_analysis_first():
    project = _project()
    _model()
    req = _requirement(project["id"])
    response = client.post(f"/api/platform/requirements/{req['id']}/plan", json={})
    assert response.status_code == 409


def test_plan_creates_test_plan(monkeypatch):
    project = _project()
    _model()
    req = _requirement(project["id"])
    _fake_llm(monkeypatch)
    client.post(f"/api/platform/requirements/{req['id']}/analyze")

    response = client.post(
        f"/api/platform/requirements/{req['id']}/plan", json={"create_plan": True}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["plan"]["person_days"] == 2.5
    assert body["plan"]["milestones"][0]["name"] == "接口测试"
    assert body["test_plan"]["name"].endswith("测试计划")
    assert body["requirement"]["status"] == "planned"

    plans = client.get(f"/api/platform/plans?project_id={project['id']}").json()
    assert any(p["id"] == body["test_plan"]["id"] for p in plans)


def test_chat_persists_messages(monkeypatch):
    project = _project()
    _model()
    req = _requirement(project["id"])

    def fake_chat_text(*args, **kwargs):
        return "导出建议限制 1 万行，并用异步任务。"

    monkeypatch.setattr("app.llm_client.chat_text", fake_chat_text)

    response = client.post(
        f"/api/platform/requirements/{req['id']}/chat",
        json={"message": "导出有什么风险？"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["analysis_updated"] is False
    assert "异步任务" in body["reply"]
    assert [m["role"] for m in body["requirement"]["messages"]] == ["user", "assistant"]


def test_chat_can_update_analysis(monkeypatch):
    project = _project()
    _model()
    req = _requirement(project["id"])

    updated = dict(ANALYSIS)
    updated["summary"] = "改过的摘要"
    reply = "好的，已补充导出范围。\n```json\n" + json.dumps(updated, ensure_ascii=False) + "\n```"

    monkeypatch.setattr("app.llm_client.chat_text", lambda *a, **k: reply)

    response = client.post(
        f"/api/platform/requirements/{req['id']}/chat",
        json={"message": "把摘要改一下"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["analysis_updated"] is True
    assert body["requirement"]["analysis"]["summary"] == "改过的摘要"
    assert "```json" not in body["reply"]
    assert "分析结果已更新" in body["reply"]
    stored = body["requirement"]["messages"][-1]["content"]
    assert "```json" not in stored
