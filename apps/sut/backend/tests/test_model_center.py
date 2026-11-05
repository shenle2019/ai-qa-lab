from uuid import uuid4

from fastapi.testclient import TestClient

from app import llm_client
from app.main import app

client = TestClient(app)


def _create_model(**overrides):
    payload = {
        "name": f"model {uuid4().hex[:8]}",
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com",
        "model_name": "deepseek-chat",
        "api_key": "sk-test-1234567890",
    }
    payload.update(overrides)
    response = client.post("/api/platform/models", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_model_never_returns_key():
    model = _create_model()
    assert "api_key" not in model
    assert model["api_key_masked"] in ("", "env:DEEPSEEK_API_KEY")
    assert model["enabled"] is True


def test_env_key_is_reported(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    model = _create_model()
    assert model["has_api_key"] is True
    assert model["api_key_masked"] == "env:DEEPSEEK_API_KEY"


def test_model_name_is_unique():
    model = _create_model()
    response = client.post(
        "/api/platform/models",
        json={
            "name": model["name"],
            "base_url": "https://api.deepseek.com",
            "model_name": "deepseek-chat",
            "api_key": "x",
        },
    )
    assert response.status_code == 409


def test_list_and_toggle_model():
    model = _create_model()
    response = client.patch(f"/api/platform/models/{model['id']}", json={"enabled": False})
    assert response.status_code == 200
    assert response.json()["enabled"] is False

    listed = client.get("/api/platform/models").json()
    assert any(item["id"] == model["id"] and item["enabled"] is False for item in listed)


def test_connectivity_test_records_call(monkeypatch):
    # CI has no DeepSeek key; the HTTP call is faked, so only presence matters.
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    model = _create_model()

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": '{"ok": true}'}}],
                "usage": {"prompt_tokens": 7, "completion_tokens": 3},
            }

    monkeypatch.setattr(llm_client.httpx, "post", lambda *args, **kwargs: FakeResponse())

    response = client.post(f"/api/platform/models/{model['id']}/test")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["latency_ms"] >= 0

    calls = client.get("/api/platform/model-calls?limit=5").json()
    latest = calls[0]
    assert latest["purpose"] == "connectivity_test"
    assert latest["status"] == "ok"
    assert latest["prompt_tokens"] + latest["completion_tokens"] == 10


def test_missing_key_is_reported(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    model = _create_model(api_key="")
    assert model["has_api_key"] is False

    response = client.post(f"/api/platform/models/{model['id']}/test")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert "API Key" in body["message"]

    calls = client.get("/api/platform/model-calls?limit=5").json()
    assert calls[0]["status"] == "error"
    assert "missing api key" in calls[0]["error"]
