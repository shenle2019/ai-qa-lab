"""Platform account directory (用户管理)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _payload(name: str = "测试账号", **overrides) -> dict:
    payload = {"name": name, "email": "qa@example.com", "role": "测试", "status": "active", "note": "初始"}
    payload.update(overrides)
    return payload


def test_create_and_list_user() -> None:
    created = client.post("/api/platform/users", json=_payload("张三"))
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "张三"
    assert body["role"] == "测试"

    listed = client.get("/api/platform/users")
    assert listed.status_code == 200
    assert any(item["id"] == body["id"] for item in listed.json())


def test_duplicate_name_conflicts() -> None:
    client.post("/api/platform/users", json=_payload("李四"))
    again = client.post("/api/platform/users", json=_payload("李四"))
    assert again.status_code == 409


def test_blank_name_rejected() -> None:
    response = client.post("/api/platform/users", json=_payload("   "))
    assert response.status_code == 400


def test_bad_role_and_status_rejected() -> None:
    assert client.post("/api/platform/users", json=_payload("角色错", role="老板")).status_code == 400
    assert client.post("/api/platform/users", json=_payload("状态错", status="sleeping")).status_code == 400


def test_patch_and_delete() -> None:
    created = client.post("/api/platform/users", json=_payload("王五")).json()
    patched = client.patch(
        f"/api/platform/users/{created['id']}",
        json={"role": "管理员", "status": "disabled", "note": "临时"},
    )
    assert patched.status_code == 200
    assert patched.json()["role"] == "管理员"
    assert patched.json()["status"] == "disabled"

    removed = client.delete(f"/api/platform/users/{created['id']}")
    assert removed.status_code == 204
    assert client.patch(f"/api/platform/users/{created['id']}", json={"role": "测试"}).status_code == 404


def test_health_exposes_auth_mode() -> None:
    body = client.get("/health").json()
    assert body["auth"] in {"dev", "production"}
