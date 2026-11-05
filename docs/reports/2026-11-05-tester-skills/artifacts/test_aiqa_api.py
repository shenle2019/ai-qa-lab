"""Corrected execution suite for ai-qa-lab.

Fixes the generator's three defects (placeholder path ids, duplicate method
names, empty request bodies) and adds the auth header. Production-specific
rules (e.g. /plans/{id}/run returns 410) are asserted explicitly.
"""
import os
import time

import pytest
import requests

BASE_URL = os.environ.get("BASE_URL", "https://ai-qa-lab-production.up.railway.app")
API_KEY = os.environ.get("APP_API_KEY", "")
H = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
STAMP = str(int(time.time()) % 100000)

PROJECT_ID = 5
PLAN_ID = 2
EXEC_ID = 3
MODEL_ID = 1
TICKET_ID = 1


def get(path, **kw):
    return requests.get(BASE_URL + path, headers=H, timeout=25, **kw)


def post(path, json=None):
    return requests.post(BASE_URL + path, headers=H, json=json, timeout=40)


def patch(path, json=None):
    return requests.patch(BASE_URL + path, headers=H, json=json, timeout=25)


def delete(path):
    return requests.delete(BASE_URL + path, headers=H, timeout=25)


def _ok(r, path, statuses=(200,)):
    assert r.status_code in statuses, f"{path} -> {r.status_code} {r.text[:180]}"


@pytest.mark.parametrize("path", [
    "/health",
    "/ready",
    "/api/platform/summary",
    "/api/platform/projects",
    "/api/platform/cases",
    "/api/platform/plans",
    "/api/platform/executions",
    "/api/platform/defects",
    "/api/platform/models",
    "/api/platform/model-calls",
    "/api/tickets",
])
def test_list_endpoints(path):
    _ok(get(path), path)


@pytest.mark.parametrize("path", [
    f"/api/platform/projects/{PROJECT_ID}",
    f"/api/platform/plans/{PLAN_ID}",
    f"/api/platform/executions/{EXEC_ID}",
    f"/api/tickets/{TICKET_ID}",
])
def test_detail_endpoints(path):
    _ok(get(path), path)


def test_execution_report():
    _ok(get(f"/api/platform/executions/{EXEC_ID}/report"), "execution report")


def test_auth_verify():
    _ok(post("/api/auth/verify"), "auth verify")


def test_ticket_crud():
    r = post("/api/tickets", {"title": "自动化回归工单"})
    _ok(r, "create ticket", (200, 201))
    tid = r.json()["id"]
    _ok(patch(f"/api/tickets/{tid}", {"status": "closed"}), "patch ticket")
    _ok(delete(f"/api/tickets/{tid}"), "delete ticket", (200, 204))
    _ok(get(f"/api/tickets/{tid}"), "get deleted ticket", (404,))


def test_create_project():
    _ok(post("/api/platform/projects", {"name": f"自动化回归项目-{STAMP}"}), "create project", (200, 201))


def test_create_case():
    _ok(post("/api/platform/cases", {"project_id": PROJECT_ID, "title": f"自动化回归用例-{STAMP}"}), "create case", (200, 201))


def test_create_plan():
    _ok(post("/api/platform/plans", {"project_id": PROJECT_ID, "name": f"自动化回归计划-{STAMP}"}), "create plan", (200, 201))


def test_create_defect():
    _ok(post("/api/platform/defects", {"project_id": PROJECT_ID, "title": f"自动化回归缺陷-{STAMP}"}), "create defect", (200, 201))


def test_create_model():
    r = post("/api/platform/models", {"name": f"自动化回归模型-{STAMP}", "provider": "deepseek", "model_name": "deepseek-chat"})
    # 409 means a duplicate name; acceptable for a create probe
    _ok(r, "create model", (200, 201, 409))


def test_patch_model():
    _ok(patch(f"/api/platform/models/{MODEL_ID}", {"name": "DeepSeek 线上"}), "patch model")


def test_submit_review():
    cases = get("/api/platform/cases").json()
    drafts = [c for c in cases if c.get("status") == "draft"]
    if not drafts:
        pytest.skip("no draft case available on the server")
    _ok(post(f"/api/platform/cases/{drafts[0]['id']}/submit-review"), "submit review", (200, 201))


def test_review():
    cases = get("/api/platform/cases").json()
    pending = [c for c in cases if c.get("status") == "pending_review"]
    if not pending:
        pytest.skip("no pending_review case available on the server")
    _ok(post(f"/api/platform/cases/{pending[0]['id']}/review", {"decision": "approved"}), "review", (200, 201))


def test_plan_run_disabled_in_production():
    # production deliberately disables client-reported results: valid body -> 410
    r = post(f"/api/platform/plans/{PLAN_ID}/run", {"results": []})
    assert r.status_code == 410, f"plan run -> {r.status_code} {r.text[:180]}"


def test_plan_execute():
    _ok(post(f"/api/platform/plans/{PLAN_ID}/execute"), "plan execute", (202,))


def test_kb_query():
    _ok(post("/api/kb/query", {"question": "如何创建工单？"}), "kb query", (200, 201))
