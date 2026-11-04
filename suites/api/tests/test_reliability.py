"""Reliability cases: repeatability, concurrency, recovery, platform safety."""

import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import requests


def _create(api, **overrides):
    payload = {"title": f"rel {uuid4().hex[:8]}", "description": "", "priority": "medium"}
    payload.update(overrides)
    return api.post("/api/tickets", json=payload)


def _concurrent(method, url, workers=10, **kwargs):
    def call(_):
        return requests.request(method, url, timeout=10, **kwargs)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(call, range(workers)))


def test_repeated_reads_are_consistent(api):
    ticket = _create(api).json()
    for _ in range(30):
        response = api.get(f"/api/tickets/{ticket['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == ticket["id"]


def test_concurrent_reads_succeed(api):
    responses = _concurrent("GET", api.base_url + "/api/tickets", workers=20)
    assert all(response.status_code == 200 for response in responses)


def test_concurrent_writes_succeed(api):
    def create(index):
        return requests.post(
            api.base_url + "/api/tickets",
            json={"title": f"concurrent {uuid4().hex[:6]}-{index}", "priority": "high"},
            timeout=10,
        )

    with ThreadPoolExecutor(max_workers=10) as pool:
        responses = list(pool.map(create, range(20)))
    assert all(response.status_code == 201 for response in responses)
    assert len({response.json()["id"] for response in responses}) == 20


def test_create_delete_recreate(api):
    title = f"recreate {uuid4().hex[:8]}"
    first = _create(api, title=title).json()
    assert api.delete(f"/api/tickets/{first['id']}").status_code == 204
    assert api.get(f"/api/tickets/{first['id']}").status_code == 404
    second = _create(api, title=title)
    assert second.status_code == 201
    assert second.json()["title"] == title
    assert isinstance(second.json()["id"], int)


def test_malformed_json_then_valid_request(api):
    bad = api.session.post(
        api.base_url + "/api/tickets",
        data='{"title":',
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert bad.status_code in (400, 422)
    assert _create(api).status_code == 201


def test_validation_error_then_valid_request(api):
    assert api.post("/api/tickets", json={"title": ""}).status_code == 422
    assert _create(api).status_code == 201


def test_delete_is_not_idempotent(api):
    ticket = _create(api).json()
    assert api.delete(f"/api/tickets/{ticket['id']}").status_code == 204
    assert api.delete(f"/api/tickets/{ticket['id']}").status_code == 404


def test_status_round_trip(api):
    ticket = _create(api).json()
    for status in ["in_progress", "closed", "open"]:
        response = api.patch(f"/api/tickets/{ticket['id']}", json={"status": status})
        assert response.status_code == 200
        assert response.json()["status"] == status


def test_repeated_create_delete_cycles(api):
    for index in range(20):
        ticket = _create(api, title=f"cycle-{uuid4().hex[:6]}-{index}").json()
        assert api.delete(f"/api/tickets/{ticket['id']}").status_code == 204
    assert api.get("/health").status_code == 200


def test_health_survives_burst(api):
    for _ in range(100):
        assert api.get("/health").status_code == 200


def test_error_detail_is_stable(api):
    first = api.get("/api/tickets/999999").json()
    second = api.get("/api/tickets/888888").json()
    assert first["detail"] == second["detail"] == "ticket not found"


def test_list_is_sorted_by_id_desc(api):
    for _ in range(3):
        _create(api)
    ids = [item["id"] for item in api.get("/api/tickets").json()]
    assert ids == sorted(ids, reverse=True)


def test_ids_increase_monotonically(api):
    ids = [_create(api).json()["id"] for _ in range(5)]
    assert ids == sorted(ids)


def test_workbench_can_call_health(api):
    response = api.post(
        "/api/workbench/send",
        json={
            "name": "health",
            "method": "GET",
            "url": api.base_url + "/health",
            "assertions": [{"type": "status", "expected": 200}],
        },
    )
    assert response.status_code == 200
    assert response.json()["passed"] is True


def test_workbench_reports_unreachable_target(api):
    response = api.post(
        "/api/workbench/send",
        json={
            "name": "down",
            "method": "GET",
            "url": "http://127.0.0.1:1/health",
            "timeout_ms": 500,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is False
    assert body["status"] is None


def test_workbench_rejects_invalid_url(api):
    response = api.post(
        "/api/workbench/send", json={"name": "bad", "method": "GET", "url": "ftp://x"}
    )
    assert response.status_code == 400


def test_workbench_blocks_metadata_address(api):
    response = api.post(
        "/api/workbench/send",
        json={"name": "meta", "method": "GET", "url": "http://169.254.169.254/latest"},
    )
    assert response.status_code == 400


def test_workbench_batch_limit(api):
    payload = {
        "requests": [
            {"name": str(index), "method": "GET", "url": api.base_url + "/health"}
            for index in range(51)
        ]
    }
    assert api.post("/api/workbench/run", json=payload).status_code == 422


def test_workbench_batch_ok(api):
    payload = {
        "requests": [
            {"name": str(index), "method": "GET", "url": api.base_url + "/health"}
            for index in range(3)
        ]
    }
    response = api.post("/api/workbench/run", json=payload)
    assert response.status_code == 200
    assert len(response.json()) == 3
    assert all(item["passed"] for item in response.json())


def _project(api):
    suffix = uuid4().hex[:8]
    return api.post(
        "/api/platform/projects", json={"name": f"rel project {suffix}", "description": ""}
    ).json()


def test_execute_without_cases_is_rejected(api):
    project = _project(api)
    plan = api.post(
        "/api/platform/plans", json={"project_id": project["id"], "name": "empty plan"}
    ).json()
    response = api.post(f"/api/platform/plans/{plan['id']}/execute", json={})
    assert response.status_code == 400


def test_executor_rejects_absolute_target(api):
    project = _project(api)
    case = api.post(
        "/api/platform/cases",
        json={
            "project_id": project["id"],
            "title": "absolute target",
            "module": "api",
            "priority": "high",
            "steps": "GET external",
            "expected": "rejected",
            "steps_json": json.dumps(
                [{"action": "GET", "target": "http://example.com/x", "data": "", "assert": "status=200"}]
            ),
        },
    ).json()
    plan = api.post(
        "/api/platform/plans", json={"project_id": project["id"], "name": "safety plan"}
    ).json()
    response = api.post(f"/api/platform/plans/{plan['id']}/execute", json={})
    assert response.status_code == 201
    body = response.json()
    assert body["failed"] == 1
    assert "相对路径" in body["results"][0]["message"]
    assert case["id"] == body["results"][0]["case_id"]


def test_missing_execution_report(api):
    assert api.get("/api/platform/executions/999999/report").status_code == 404


def test_duplicate_model_name_is_rejected(api):
    name = f"rel model {uuid4().hex[:8]}"
    payload = {"name": name, "base_url": "https://api.deepseek.com", "api_key": "sk-abcdefgh1234"}
    assert api.post("/api/platform/models", json=payload).status_code == 201
    assert api.post("/api/platform/models", json=payload).status_code == 409


def test_model_key_is_masked(api):
    response = api.post(
        "/api/platform/models",
        json={
            "name": f"mask {uuid4().hex[:8]}",
            "base_url": "https://api.deepseek.com",
            "api_key": "sk-abcdefgh1234",
        },
    )
    body = response.json()
    assert "api_key" not in body
    assert body["api_key_masked"].endswith("1234")


def test_seed_is_idempotent(api):
    first = api.post("/api/platform/seed").json()
    second = api.post("/api/platform/seed").json()
    assert first["projects"] == second["projects"]
    assert first["cases"] == second["cases"]


def test_server_survives_bad_body_and_stays_healthy(api):
    api.session.post(
        api.base_url + "/api/tickets",
        data="not json at all",
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert api.get("/health").json()["status"] == "ok"
