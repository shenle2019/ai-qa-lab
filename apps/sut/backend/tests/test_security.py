from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_read_endpoints_stay_public_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_API_KEY", "secret-key")
    assert client.get("/health").status_code == 200
    assert client.get("/api/tickets").status_code == 200


def test_write_endpoints_require_key_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_API_KEY", "secret-key")
    denied = client.post("/api/tickets", json={"title": "blocked"})
    assert denied.status_code == 401
    assert denied.headers["www-authenticate"] == "Bearer"

    wrong = client.post(
        "/api/tickets",
        json={"title": "blocked"},
        headers={"Authorization": "Bearer wrong"},
    )
    assert wrong.status_code == 401

    allowed = client.post(
        "/api/tickets",
        json={"title": "allowed"},
        headers={"X-API-Key": "secret-key"},
    )
    assert allowed.status_code == 201


def test_readonly_post_stays_public_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_API_KEY", "secret-key")
    response = client.post("/api/kb/query", json={"question": "如何关闭工单", "top_k": 3})
    assert response.status_code == 200
    assert "answer" in response.json()

    # The workbench proxy executes server-side requests, so it stays gated.
    assert client.post(
        "/api/workbench/send",
        json={"name": "x", "method": "GET", "url": "/health"},
    ).status_code == 401


def test_key_verification_endpoint(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_API_KEY", "secret-key")
    assert client.post("/api/auth/verify").status_code == 401
    ok = client.post("/api/auth/verify", headers={"Authorization": "Bearer secret-key"})
    assert ok.status_code == 200
    assert ok.json() == {"ok": True}


def test_missing_server_key_fails_closed(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("APP_API_KEY", raising=False)
    response = client.post("/api/tickets", json={"title": "x"})
    assert response.status_code == 401


def test_ssrf_blocks_loopback_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_API_KEY", "secret-key")
    response = client.post(
        "/api/workbench/send",
        json={"name": "loop", "method": "GET", "url": "http://127.0.0.1:8000/health"},
        headers={"Authorization": "Bearer secret-key"},
    )
    assert response.status_code == 400
    assert "blocked" in response.json()["detail"]


def test_ssrf_blocks_private_ip_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_API_KEY", "secret-key")
    response = client.post(
        "/api/workbench/send",
        json={"name": "private", "method": "GET", "url": "http://10.0.0.1/"},
        headers={"Authorization": "Bearer secret-key"},
    )
    assert response.status_code == 400


def test_security_headers_present():
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers
    assert response.headers["X-Request-ID"]


def test_ready_checks_database():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
