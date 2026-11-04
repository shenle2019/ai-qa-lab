from uuid import uuid4


def _title(prefix: str = "crud") -> str:
    return f"{prefix} {uuid4().hex[:8]}"


def _create(api, **overrides):
    payload = {"title": _title(), "description": "crud suite", "priority": "medium"}
    payload.update(overrides)
    response = api.post("/api/tickets", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_minimal_returns_201(api):
    response = api.post("/api/tickets", json={"title": _title("minimal")})
    assert response.status_code == 201
    body = response.json()
    assert body["title"].startswith("minimal")
    assert body["status"] == "open"
    assert body["priority"] == "medium"


def test_create_defaults(api):
    body = _create(api)
    assert body["status"] == "open"
    assert body["priority"] == "medium"
    assert body["description"] == "crud suite"


def test_create_high_priority(api):
    body = _create(api, priority="high")
    assert body["priority"] == "high"


def test_create_low_priority(api):
    body = _create(api, priority="low")
    assert body["priority"] == "low"


def test_create_with_description(api):
    body = _create(api, description="repro steps")
    assert body["description"] == "repro steps"


def test_create_empty_description(api):
    body = _create(api, description="")
    assert body["description"] == ""


def test_create_title_200_chars(api):
    body = _create(api, title="x" * 200)
    assert len(body["title"]) == 200


def test_create_title_201_chars_rejected(api):
    response = api.post("/api/tickets", json={"title": "x" * 201})
    assert response.status_code == 422


def test_create_blank_title_rejected(api):
    response = api.post("/api/tickets", json={"title": ""})
    assert response.status_code == 422


def test_create_missing_title_rejected(api):
    response = api.post("/api/tickets", json={"description": "no title"})
    assert response.status_code == 422


def test_create_single_char_title(api):
    body = _create(api, title="x")
    assert body["title"] == "x"


def test_get_created_ticket(api):
    body = _create(api)
    response = api.get(f"/api/tickets/{body['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == body["id"]


def test_get_missing_ticket_returns_404(api):
    response = api.get("/api/tickets/99999999")
    assert response.status_code == 404


def test_list_contains_created_ticket(api):
    body = _create(api)
    ids = [item["id"] for item in api.get("/api/tickets").json()]
    assert body["id"] in ids


def test_list_is_newest_first(api):
    first = _create(api, title=_title("first"))
    second = _create(api, title=_title("second"))
    ids = [item["id"] for item in api.get("/api/tickets").json()]
    assert ids.index(second["id"]) < ids.index(first["id"])


def test_update_status_in_progress(api):
    body = _create(api)
    response = api.patch(f"/api/tickets/{body['id']}", json={"status": "in_progress"})
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_update_status_closed(api):
    body = _create(api)
    response = api.patch(f"/api/tickets/{body['id']}", json={"status": "closed"})
    assert response.status_code == 200
    assert response.json()["status"] == "closed"


def test_update_priority_high(api):
    body = _create(api)
    response = api.patch(f"/api/tickets/{body['id']}", json={"priority": "high"})
    assert response.status_code == 200
    assert response.json()["priority"] == "high"


def test_update_priority_low(api):
    body = _create(api)
    response = api.patch(f"/api/tickets/{body['id']}", json={"priority": "low"})
    assert response.status_code == 200
    assert response.json()["priority"] == "low"


def test_update_status_and_priority(api):
    body = _create(api)
    response = api.patch(
        f"/api/tickets/{body['id']}",
        json={"status": "in_progress", "priority": "high"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "in_progress"
    assert payload["priority"] == "high"


def test_update_invalid_status_rejected(api):
    body = _create(api)
    response = api.patch(f"/api/tickets/{body['id']}", json={"status": "done"})
    assert response.status_code == 422


def test_update_invalid_priority_rejected(api):
    body = _create(api)
    response = api.patch(f"/api/tickets/{body['id']}", json={"priority": "urgent"})
    assert response.status_code == 422


def test_update_missing_ticket_returns_404(api):
    response = api.patch("/api/tickets/99999999", json={"status": "closed"})
    assert response.status_code == 404


def test_empty_update_keeps_values(api):
    body = _create(api)
    response = api.patch(f"/api/tickets/{body['id']}", json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == body["status"]
    assert payload["priority"] == body["priority"]


def test_delete_ticket_returns_204(api):
    body = _create(api)
    response = api.delete(f"/api/tickets/{body['id']}")
    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_ticket_returns_404(api):
    response = api.delete("/api/tickets/99999999")
    assert response.status_code == 404


def test_deleted_ticket_is_gone(api):
    body = _create(api)
    api.delete(f"/api/tickets/{body['id']}")
    assert api.get(f"/api/tickets/{body['id']}").status_code == 404


def test_deleted_ticket_not_in_list(api):
    body = _create(api)
    api.delete(f"/api/tickets/{body['id']}")
    ids = [item["id"] for item in api.get("/api/tickets").json()]
    assert body["id"] not in ids


def test_delete_twice_returns_404(api):
    body = _create(api)
    assert api.delete(f"/api/tickets/{body['id']}").status_code == 204
    assert api.delete(f"/api/tickets/{body['id']}").status_code == 404
