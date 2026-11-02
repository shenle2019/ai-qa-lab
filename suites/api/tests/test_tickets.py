import uuid


def _title(prefix: str = "工单") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def test_create_ticket_uses_defaults(api):
    title = _title()

    response = api.post("/api/tickets", json={"title": title})

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["title"] == title
    assert body["description"] == ""
    assert body["status"] == "open"
    assert body["priority"] == "medium"


def test_create_ticket_with_explicit_fields(api):
    title = _title("登录失败")

    response = api.post(
        "/api/tickets",
        json={
            "title": title,
            "description": "验证码不显示，无法登录",
            "priority": "high",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == title
    assert body["description"] == "验证码不显示，无法登录"
    assert body["priority"] == "high"


def test_get_and_list_ticket(api):
    created = api.post("/api/tickets", json={"title": _title()}).json()

    fetched = api.get(f"/api/tickets/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]

    listed = api.get("/api/tickets")
    assert listed.status_code == 200
    assert any(item["id"] == created["id"] for item in listed.json())


def test_patch_ticket_status(api):
    created = api.post("/api/tickets", json={"title": _title()}).json()

    updated = api.patch(
        f"/api/tickets/{created['id']}",
        json={"status": "closed"},
    )

    assert updated.status_code == 200
    assert updated.json()["status"] == "closed"


def test_patch_ticket_priority_only(api):
    created = api.post("/api/tickets", json={"title": _title()}).json()

    updated = api.patch(
        f"/api/tickets/{created['id']}",
        json={"priority": "low"},
    )

    assert updated.status_code == 200
    body = updated.json()
    assert body["priority"] == "low"
    assert body["status"] == "open"
