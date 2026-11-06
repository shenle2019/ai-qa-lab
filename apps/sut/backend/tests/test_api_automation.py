"""API automation: spec import, endpoint CRUD, debug, case/scenario execution."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class _Handler(BaseHTTPRequestHandler):
    """Tiny SUT used to exercise real HTTP calls."""

    def log_message(self, *args):  # noqa: D102 - silence test output
        return

    def _send(self, code: int, payload: dict | None = None) -> None:
        body = b"" if payload is None else json.dumps(payload).encode("utf-8")
        self.send_response(code)
        if payload is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - http.server contract
        if self.path.startswith("/api/tickets/999"):
            self._send(404, {"detail": "not found"})
        elif self.path.startswith("/api/tickets/7"):
            self._send(200, {"data": {"id": 7, "status": "open", "title": "打印机坏了"}})
        elif self.path.startswith("/api/tickets"):
            self._send(200, {"items": [{"id": 7}], "total": 1})
        else:
            self._send(404, {"detail": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - http.server contract
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            payload = {}
        self._send(201, {"data": {"id": 7, "title": payload.get("title", "")}})

    def do_DELETE(self) -> None:  # noqa: N802 - http.server contract
        self._send(204, None)


@pytest.fixture(scope="module")
def sut_base() -> str:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "工单服务", "version": "1.0.0"},
    "servers": [{"url": "http://127.0.0.1:1"}],
    "paths": {
        "/api/tickets": {
            "get": {
                "summary": "查询工单列表",
                "tags": ["tickets"],
                "parameters": [
                    {"name": "status", "in": "query", "required": False, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "ok"}},
            },
            "post": {
                "summary": "创建工单",
                "tags": ["tickets"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["title"],
                                "properties": {
                                    "title": {"type": "string", "description": "标题"},
                                    "priority": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "responses": {"201": {"description": "created"}},
            },
        },
        "/api/tickets/{ticket_id}": {
            "get": {
                "summary": "查询工单详情",
                "tags": ["tickets"],
                "parameters": [
                    {
                        "name": "ticket_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
                "responses": {"200": {"description": "ok"}, "404": {"description": "missing"}},
            }
        },
    },
}

SPEC_YAML = """
openapi: 3.0.0
info:
  title: 订单服务
  version: 2.0.0
servers:
  - url: http://127.0.0.1:1
paths:
  /api/orders:
    get:
      summary: 查询订单
      tags: [orders]
      responses:
        '200':
          description: ok
"""


_PROJECT_SEQ = {"n": 0}


def _project() -> int:
    """Create a dedicated project per call so imports never collide."""
    _PROJECT_SEQ["n"] += 1
    response = client.post(
        "/api/platform/projects",
        json={"name": f"接口自动化项目 {_PROJECT_SEQ['n']}"},
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def test_import_openapi_json() -> None:
    project_id = _project()
    response = client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(SPEC)},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["imported"] == 3
    assert body["name"] == "工单服务"
    assert body["base_url"] == "http://127.0.0.1:1"

    endpoints = client.get(
        "/api/platform/api-endpoints", params={"project_id": project_id}
    ).json()
    assert len(endpoints) == 3
    methods = {item["method"] for item in endpoints}
    assert methods == {"GET", "POST"}
    post = next(item for item in endpoints if item["method"] == "POST")
    fields = post["body"]["fields"]
    assert {item["name"] for item in fields} == {"title", "priority"}
    assert any(item["required"] for item in fields if item["name"] == "title")


def test_import_openapi_yaml() -> None:
    project_id = _project()
    response = client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": SPEC_YAML},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["imported"] == 1
    assert body["name"] == "订单服务"
    assert body["spec_version"] == "3.0.0"


def test_import_rejects_garbage() -> None:
    project_id = _project()
    response = client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": "这不是接口文档"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]


def test_endpoint_crud_and_modules() -> None:
    project_id = _project()
    created = client.post(
        "/api/platform/api-endpoints",
        json={
            "project_id": project_id,
            "method": "get",
            "path": "/api/health",
            "name": "健康检查",
            "module": "系统",
        },
    )
    assert created.status_code == 201, created.text
    endpoint_id = created.json()["id"]
    assert created.json()["method"] == "GET"

    patched = client.patch(
        f"/api/platform/api-endpoints/{endpoint_id}",
        json={"name": "健康检查 v2", "module": "基础"},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "健康检查 v2"
    assert patched.json()["module"] == "基础"

    modules = client.get(
        "/api/platform/api-endpoints/modules", params={"project_id": project_id}
    ).json()
    assert any(item["module"] == "基础" for item in modules)

    deleted = client.delete(f"/api/platform/api-endpoints/{endpoint_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/platform/api-endpoints/{endpoint_id}").status_code == 404


def test_invalid_method_rejected() -> None:
    project_id = _project()
    response = client.post(
        "/api/platform/api-endpoints",
        json={"project_id": project_id, "method": "FETCH", "path": "/api/x"},
    )
    assert response.status_code == 400


def _first_endpoint(project_id: int, method: str, path: str) -> dict:
    endpoints = client.get(
        "/api/platform/api-endpoints", params={"project_id": project_id}
    ).json()
    for item in endpoints:
        if item["method"] == method and item["path"] == path:
            return item
    raise AssertionError(f"endpoint {method} {path} not found")


def test_debug_endpoint_records_run(sut_base: str) -> None:
    project_id = _project()
    client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(SPEC)},
    )
    endpoint = _first_endpoint(project_id, "GET", "/api/tickets")

    response = client.post(
        f"/api/platform/api-endpoints/{endpoint['id']}/debug",
        json={"base_url": sut_base, "expect_status": 200},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "passed"
    assert body["status_code"] == 200
    assert body["response"]["json"]["total"] == 1

    runs = client.get("/api/platform/api-runs", params={"project_id": project_id}).json()
    assert runs and runs[0]["id"] == body["id"]
    assert runs[0]["kind"] == "debug"


def test_debug_failure_is_recorded(sut_base: str) -> None:
    project_id = _project()
    client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(SPEC)},
    )
    endpoint = _first_endpoint(project_id, "GET", "/api/tickets")
    response = client.post(
        f"/api/platform/api-endpoints/{endpoint['id']}/debug",
        json={"base_url": sut_base, "expect_status": 500},
    )
    body = response.json()
    assert body["status"] == "failed"
    assert "500" in (body["error"] or "")


def test_single_case_pass(sut_base: str) -> None:
    project_id = _project()
    client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(SPEC)},
    )
    endpoint = _first_endpoint(project_id, "GET", "/api/tickets")

    created = client.post(
        "/api/platform/api-cases",
        json={
            "project_id": project_id,
            "endpoint_id": endpoint["id"],
            "kind": "case",
            "title": "工单列表返回 200",
            "steps": [
                {
                    "name": "查列表",
                    "method": "GET",
                    "url": "/api/tickets",
                    "expect": {"status": 200, "contains": "total"},
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    case_id = created.json()["id"]

    run = client.post(
        f"/api/platform/api-cases/{case_id}/run",
        params={"base_url": sut_base},
    )
    body = run.json()
    assert run.status_code == 200, run.text
    assert body["status"] == "passed"
    assert body["steps"][0]["status_code"] == 200


def test_case_run_uses_asset_base_url(sut_base: str) -> None:
    project_id = _project()
    imported = client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(SPEC)},
    ).json()
    client.patch(
        f"/api/platform/api-endpoints/{_first_endpoint(project_id, 'GET', '/api/tickets')['id']}",
        json={"name": "查询工单列表"},
    )
    assert imported["base_url"]

    endpoint = _first_endpoint(project_id, "GET", "/api/tickets")
    asset_id = endpoint["asset_id"]
    # 用真实 SUT 覆盖 base_url：删掉旧资产，重新导入一份指向本地服务的 spec
    client.delete(f"/api/platform/api-assets/{asset_id}")
    spec = json.loads(json.dumps(SPEC))
    spec["servers"] = [{"url": sut_base}]
    client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(spec)},
    )
    endpoint = _first_endpoint(project_id, "GET", "/api/tickets")
    case = client.post(
        "/api/platform/api-cases",
        json={
            "project_id": project_id,
            "endpoint_id": endpoint["id"],
            "title": "用资产 base_url 跑",
            "steps": [{"method": "GET", "url": "/api/tickets", "expect": {"status": 200}}],
        },
    ).json()
    run = client.post(f"/api/platform/api-cases/{case['id']}/run")
    assert run.status_code == 200, run.text
    assert run.json()["status"] == "passed"


def test_scenario_data_flow(sut_base: str) -> None:
    project_id = _project()
    client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(SPEC)},
    )
    create_ep = _first_endpoint(project_id, "POST", "/api/tickets")
    detail_ep = _first_endpoint(project_id, "GET", "/api/tickets/{ticket_id}")

    case = client.post(
        "/api/platform/api-cases",
        json={
            "project_id": project_id,
            "kind": "scenario",
            "title": "创建后按 id 查详情",
            "steps": [
                {
                    "name": "创建工单",
                    "method": "POST",
                    "url": "/api/tickets",
                    "body": {"title": "打印机坏了"},
                    "extract": {"ticket_id": "data.id"},
                    "expect": {"status": 201},
                },
                {
                    "name": "查详情",
                    "method": "GET",
                    "url": "/api/tickets/{{ticket_id}}",
                    "expect": {"status": 200, "json_path": "data.id", "equals": 7},
                },
            ],
        },
    )
    assert case.status_code == 201, case.text
    case_id = case.json()["id"]
    assert case.json()["endpoint_id"] is None
    assert detail_ep["id"]

    run = client.post(
        f"/api/platform/api-cases/{case_id}/run", params={"base_url": sut_base}
    )
    body = run.json()
    assert run.status_code == 200, run.text
    assert body["status"] == "passed", body
    assert body["variables"]["ticket_id"] == 7
    assert len(body["steps"]) == 2


def test_scenario_stops_at_failure(sut_base: str) -> None:
    project_id = _project()
    client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(SPEC)},
    )
    case = client.post(
        "/api/platform/api-cases",
        json={
            "project_id": project_id,
            "kind": "scenario",
            "title": "第二步失败就停",
            "steps": [
                {"method": "GET", "url": "/api/tickets", "expect": {"status": 200}},
                {"method": "GET", "url": "/api/tickets/999", "expect": {"status": 200}},
                {"method": "GET", "url": "/api/tickets", "expect": {"status": 200}},
            ],
        },
    ).json()
    run = client.post(
        f"/api/platform/api-cases/{case['id']}/run", params={"base_url": sut_base}
    ).json()
    assert run["status"] == "failed"
    assert len(run["steps"]) == 2
    assert run["error"]


def test_case_validation() -> None:
    project_id = _project()
    empty = client.post(
        "/api/platform/api-cases",
        json={"project_id": project_id, "title": "没有步骤", "steps": []},
    )
    assert empty.status_code == 400
    missing = client.post("/api/platform/api-cases/9999/run")
    assert missing.status_code == 404


def test_generate_cases_with_fake_model(monkeypatch) -> None:
    project_id = _project()
    client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(SPEC)},
    )
    endpoint = _first_endpoint(project_id, "GET", "/api/tickets")

    def fake_chat_json(db, config, messages, **kwargs):
        return {
            "cases": [
                {
                    "title": "未登录查询工单列表返回 401",
                    "module": "tickets",
                    "steps": [
                        {
                            "name": "匿名请求",
                            "method": "GET",
                            "url": "/api/tickets",
                            "expect": {"status": 401},
                        }
                    ],
                    "expected": "未携带凭证时应被拒绝",
                }
            ]
        }

    monkeypatch.setattr(
        "app.skills.builtin.api_case_generate.chat_json", fake_chat_json
    )
    # 需要至少一个 enabled 模型
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

    response = client.post(
        "/api/platform/api-cases/generate",
        json={"endpoint_id": endpoint["id"], "count": 3},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["count"] == 1
    assert body["cases"][0]["status"] == "draft"
    assert body["cases"][0]["source"] == "ai"
    assert body["cases"][0]["steps"][0]["url"] == "/api/tickets"


def test_generate_scenario_with_fake_model(monkeypatch) -> None:
    project_id = _project()
    client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(SPEC)},
    )
    endpoints = client.get(
        "/api/platform/api-endpoints", params={"project_id": project_id}
    ).json()
    ids = [item["id"] for item in endpoints][:2]

    def fake_chat_json(db, config, messages, **kwargs):
        return {
            "title": "创建并查询工单",
            "steps": [
                {
                    "name": "创建",
                    "method": "POST",
                    "url": "/api/tickets",
                    "body": {"title": "x"},
                    "extract": {"ticket_id": "data.id"},
                    "expect": {"status": 201},
                },
                {
                    "name": "查询",
                    "method": "GET",
                    "url": "/api/tickets/{{ticket_id}}",
                    "expect": {"status": 200},
                },
            ],
            "expected": "创建后能查到",
        }

    monkeypatch.setattr(
        "app.skills.builtin.api_scenario_generate.chat_json", fake_chat_json
    )
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

    response = client.post(
        "/api/platform/api-cases/generate-scenario",
        json={"project_id": project_id, "endpoint_ids": ids, "goal": "创建后查询"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["kind"] == "scenario"
    assert len(body["steps"]) == 2
    assert "{{ticket_id}}" in body["steps"][1]["url"]


def test_diagnose_rejects_passed_run(sut_base: str) -> None:
    project_id = _project()
    client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(SPEC)},
    )
    endpoint = _first_endpoint(project_id, "GET", "/api/tickets")
    run = client.post(
        f"/api/platform/api-endpoints/{endpoint['id']}/debug",
        json={"base_url": sut_base, "expect_status": 200},
    ).json()
    response = client.post(f"/api/platform/api-runs/{run['id']}/diagnose")
    assert response.status_code == 400


def test_diagnose_failed_run_with_fake_model(monkeypatch) -> None:
    project_id = _project()
    client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(SPEC)},
    )
    endpoint = _first_endpoint(project_id, "GET", "/api/tickets")
    run = client.post(
        f"/api/platform/api-endpoints/{endpoint['id']}/debug",
        json={"base_url": "http://127.0.0.1:1", "expect_status": 200},
    ).json()
    assert run["status"] == "failed"

    def fake_chat_text(db, config, messages, **kwargs):
        return "结论：服务端不可达。依据：请求地址 127.0.0.1:1，连接被拒绝。建议：把 base_url 指向可用的测试环境。"

    monkeypatch.setattr("app.api_executor.chat_text", fake_chat_text)
    response = client.post(f"/api/platform/api-runs/{run['id']}/diagnose")
    assert response.status_code == 200, response.text
    assert "服务端不可达" in response.json()["ai_root_cause"]


def test_delete_endpoint_cascades_cases() -> None:
    project_id = _project()
    client.post(
        "/api/platform/api-assets/import",
        json={"project_id": project_id, "spec": json.dumps(SPEC)},
    )
    endpoint = _first_endpoint(project_id, "GET", "/api/tickets")
    case = client.post(
        "/api/platform/api-cases",
        json={
            "project_id": project_id,
            "endpoint_id": endpoint["id"],
            "title": "会被级联删掉",
            "steps": [{"method": "GET", "url": "/api/tickets"}],
        },
    ).json()
    assert client.delete(f"/api/platform/api-endpoints/{endpoint['id']}").status_code == 204
    cases = client.get(
        "/api/platform/api-cases", params={"project_id": project_id}
    ).json()
    assert all(item["id"] != case["id"] for item in cases)
