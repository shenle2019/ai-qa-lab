def test_health_returns_ok(api):
    response = api.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "sut"
    assert body["version"]


def test_openapi_schema_is_available(api):
    response = api.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/tickets" in paths
    assert "/api/tickets/{ticket_id}" in paths
    assert "/api/kb/query" in paths
