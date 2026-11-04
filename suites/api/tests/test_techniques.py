"""Ticket API cases designed with equivalence partitioning, boundary values,
error guessing and scenario testing."""

from uuid import uuid4

import pytest


def _create(api, **overrides):
    payload = {
        "title": f"tech {uuid4().hex[:8]}",
        "description": "",
        "priority": "medium",
    }
    payload.update(overrides)
    return api.post("/api/tickets", json=payload)


def _find(api, title):
    return next((item for item in api.get("/api/tickets").json() if item["title"] == title), None)


@pytest.mark.parametrize("length", [1, 2, 10, 50, 100, 199, 200])
def test_title_valid_equivalence_and_boundary(api, length):
    title = "x" * length
    response = _create(api, title=title)
    assert response.status_code == 201, response.text
    assert len(response.json()["title"]) == length


@pytest.mark.parametrize("length", [0, 201, 1000])
def test_title_invalid_equivalence_and_boundary(api, length):
    response = _create(api, title="x" * length)
    assert response.status_code == 422


@pytest.mark.parametrize("priority", ["low", "medium", "high"])
def test_priority_valid_equivalence(api, priority):
    response = _create(api, priority=priority)
    assert response.status_code == 201
    assert response.json()["priority"] == priority


@pytest.mark.parametrize("priority", ["urgent", "", "HIGH", "0"])
def test_priority_invalid_equivalence(api, priority):
    response = _create(api, priority=priority)
    assert response.status_code == 422


@pytest.mark.parametrize("length", [0, 1, 4999, 5000])
def test_description_valid_boundary(api, length):
    response = _create(api, description="d" * length)
    assert response.status_code == 201
    assert len(response.json()["description"]) == length


def test_description_over_limit(api):
    response = _create(api, description="d" * 5001)
    assert response.status_code == 422


def test_ticket_lifecycle_scenario(api):
    created = _create(api, title=f"lifecycle {uuid4().hex[:8]}", priority="high")
    assert created.status_code == 201
    ticket = created.json()

    fetched = api.get(f"/api/tickets/{ticket['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["priority"] == "high"

    updated = api.patch(f"/api/tickets/{ticket['id']}", json={"status": "in_progress"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"

    closed = api.patch(f"/api/tickets/{ticket['id']}", json={"status": "closed"})
    assert closed.json()["status"] == "closed"

    deleted = api.delete(f"/api/tickets/{ticket['id']}")
    assert deleted.status_code == 204
    assert api.get(f"/api/tickets/{ticket['id']}").status_code == 404


@pytest.mark.parametrize("status", ["open", "in_progress", "closed"])
def test_status_update_equivalence(api, status):
    ticket = _create(api).json()
    response = api.patch(f"/api/tickets/{ticket['id']}", json={"status": status})
    assert response.status_code == 200
    assert response.json()["status"] == status


@pytest.mark.parametrize("status", ["done", "", "OPEN", "closed "])
def test_status_update_invalid(api, status):
    ticket = _create(api).json()
    response = api.patch(f"/api/tickets/{ticket['id']}", json={"status": status})
    assert response.status_code == 422


def test_partial_update_keeps_other_fields(api):
    ticket = _create(api, priority="low").json()
    response = api.patch(f"/api/tickets/{ticket['id']}", json={"status": "closed"})
    assert response.json()["priority"] == "low"
    assert response.json()["title"] == ticket["title"]


def test_update_missing_ticket(api):
    assert api.patch("/api/tickets/999999", json={"status": "closed"}).status_code == 404


def test_get_missing_ticket(api):
    assert api.get("/api/tickets/999999").status_code == 404


def test_delete_missing_ticket(api):
    assert api.delete("/api/tickets/999999").status_code == 404


def test_duplicate_titles_are_allowed(api):
    title = f"duplicate {uuid4().hex[:8]}"
    first = _create(api, title=title)
    second = _create(api, title=title)
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


def test_unicode_title(api):
    title = f"中文工单-打印机故障-{uuid4().hex[:6]}"
    assert _create(api, title=title).json()["title"] == title


def test_emoji_title(api):
    title = f"支付失败 🔥🧾 {uuid4().hex[:6]}"
    assert _create(api, title=title).json()["title"] == title


@pytest.mark.parametrize(
    "title",
    [
        "quotes ' \" `",
        "line1\nline2\tend",
        "%%%___---",
        "a" * 1 + "  " + "b",
    ],
)
def test_special_characters_are_preserved(api, title):
    response = _create(api, title=title)
    assert response.status_code == 201
    assert response.json()["title"] == title


def test_sql_injection_is_stored_literally(api):
    title = "'; DROP TABLE tickets; --"
    response = _create(api, title=title)
    assert response.status_code == 201
    assert _find(api, title) is not None
    assert api.get("/api/tickets").status_code == 200


def test_xss_payload_is_returned_as_data(api):
    title = '<script>alert("x")</script>'
    response = _create(api, title=title)
    assert response.json()["title"] == title


@pytest.mark.parametrize(
    "payload",
    [
        {"description": "missing title"},
        {"title": None},
        {"title": 123},
        {"title": True},
        {"title": ["a"]},
    ],
)
def test_invalid_title_payloads(api, payload):
    assert api.post("/api/tickets", json=payload).status_code == 422


def test_unknown_fields_are_ignored(api):
    response = _create(api, unknown="ignored", another=1)
    assert response.status_code == 201
    assert "unknown" not in response.json()


def test_created_ticket_appears_in_list(api):
    ticket = _create(api).json()
    assert any(item["id"] == ticket["id"] for item in api.get("/api/tickets").json())


def test_bulk_create_scenario(api):
    prefix = f"bulk {uuid4().hex[:6]}"
    ids = []
    for index in range(10):
        response = _create(api, title=f"{prefix}-{index}")
        assert response.status_code == 201
        ids.append(response.json()["id"])
    listed = {item["id"] for item in api.get("/api/tickets").json()}
    assert set(ids).issubset(listed)
