from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_list_and_get_ticket():
    created = client.post(
        "/api/tickets",
        json={"title": "登录失败", "description": "验证码不显示", "priority": "high"},
    )
    assert created.status_code == 201
    ticket = created.json()
    assert ticket["id"] > 0
    assert ticket["status"] == "open"
    assert ticket["priority"] == "high"

    listed = client.get("/api/tickets")
    assert listed.status_code == 200
    assert any(item["id"] == ticket["id"] for item in listed.json())

    fetched = client.get(f"/api/tickets/{ticket['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "登录失败"


def test_get_missing_ticket_returns_404():
    response = client.get("/api/tickets/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "ticket not found"


def test_update_ticket_status():
    created = client.post("/api/tickets", json={"title": "导出报表"}).json()

    updated = client.patch(
        f"/api/tickets/{created['id']}",
        json={"status": "closed"},
    )

    assert updated.status_code == 200
    assert updated.json()["status"] == "closed"


def test_create_ticket_rejects_empty_title():
    response = client.post("/api/tickets", json={"title": ""})

    assert response.status_code == 422


def test_mock_knowledge_base_query():
    response = client.post(
        "/api/kb/query",
        json={"question": "工单如何升级优先级？", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["top_k"] == 3
    assert "工单如何升级优先级？" in body["answer"]
