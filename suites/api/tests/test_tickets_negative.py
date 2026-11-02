import uuid


def _title() -> str:
    return f"negative-{uuid.uuid4().hex[:8]}"


def test_get_missing_ticket_returns_404(api):
    response = api.get("/api/tickets/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "ticket not found"


def test_non_integer_ticket_id_returns_422(api):
    response = api.get("/api/tickets/abc")

    assert response.status_code == 422


def test_create_missing_title_returns_422(api):
    response = api.post("/api/tickets", json={})

    assert response.status_code == 422


def test_create_empty_title_returns_422(api):
    response = api.post("/api/tickets", json={"title": ""})

    assert response.status_code == 422


def test_create_overlong_title_returns_422(api):
    response = api.post("/api/tickets", json={"title": "x" * 201})

    assert response.status_code == 422


def test_create_overlong_description_returns_422(api):
    response = api.post(
        "/api/tickets",
        json={"title": _title(), "description": "x" * 5001},
    )

    assert response.status_code == 422


def test_create_invalid_priority_returns_422(api):
    response = api.post(
        "/api/tickets",
        json={"title": _title(), "priority": "urgent"},
    )

    assert response.status_code == 422


def test_patch_invalid_status_returns_422(api):
    created = api.post("/api/tickets", json={"title": _title()}).json()

    response = api.patch(
        f"/api/tickets/{created['id']}",
        json={"status": "done"},
    )

    assert response.status_code == 422


def test_patch_missing_ticket_returns_404(api):
    response = api.patch("/api/tickets/999999", json={"status": "closed"})

    assert response.status_code == 404
