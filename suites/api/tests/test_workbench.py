def test_workbench_send_passes_assertions(api, base_url):
    response = api.post(
        "/api/workbench/send",
        json={
            "name": "health",
            "method": "GET",
            "url": f"{base_url}/health",
            "headers": {"Accept": "application/json"},
            "assertions": [
                {"type": "status", "expected": 200},
                {"type": "json_path_equals", "path": "$.status", "expected": "ok"},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["status"] == 200
    assert body["elapsed_ms"] >= 0
    assert body["failures"] == []
    assert "sut" in body["body_preview"]


def test_workbench_send_reports_failed_assertion(api, base_url):
    response = api.post(
        "/api/workbench/send",
        json={
            "name": "wrong-status",
            "method": "GET",
            "url": f"{base_url}/health",
            "assertions": [{"type": "status", "expected": 201}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is False
    assert any("status expected 201" in failure for failure in body["failures"])


def test_workbench_run_collection(api, base_url):
    response = api.post(
        "/api/workbench/run",
        json={
            "requests": [
                {
                    "name": "health",
                    "method": "GET",
                    "url": f"{base_url}/health",
                    "assertions": [{"type": "status", "expected": 200}],
                },
                {
                    "name": "tickets",
                    "method": "GET",
                    "url": f"{base_url}/api/tickets",
                    "assertions": [
                        {"type": "status", "expected": 200},
                        {"type": "json_path_exists", "path": "$[0].id"},
                    ],
                },
            ]
        },
    )

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    assert all(item["passed"] for item in results)


def test_workbench_rejects_non_http_url(api):
    response = api.post(
        "/api/workbench/send",
        json={"name": "bad", "url": "file:///etc/passwd"},
    )

    assert response.status_code == 400


def test_workbench_body_contains_assertion(api, base_url):
    response = api.post(
        "/api/workbench/send",
        json={
            "name": "contains",
            "method": "GET",
            "url": f"{base_url}/health",
            "assertions": [{"type": "body_contains", "expected": "service"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["passed"] is True
