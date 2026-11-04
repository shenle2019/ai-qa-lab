"""Compatibility cases: payload formats, HTTP semantics, encodings, schema stability."""

import json
from datetime import datetime
from uuid import uuid4

import pytest


def _payload(**overrides):
    payload = {"title": f"compat {uuid4().hex[:8]}", "description": "", "priority": "medium"}
    payload.update(overrides)
    return payload


def _post_raw(api, body: str, content_type: str | None):
    headers = {"Content-Type": content_type} if content_type else {}
    return api.session.post(api.base_url + "/api/tickets", data=body, headers=headers, timeout=10)


def test_json_with_utf8_charset(api):
    response = api.session.post(
        api.base_url + "/api/tickets",
        json=_payload(title="字符集兼容"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=10,
    )
    assert response.status_code == 201
    assert response.json()["title"] == "字符集兼容"


def test_text_plain_json_body_is_rejected(api):
    response = _post_raw(api, json.dumps(_payload()), "text/plain")
    assert response.status_code == 422


def test_missing_content_type_still_parses_json(api):
    response = _post_raw(api, json.dumps(_payload()), None)
    assert response.status_code == 201


def test_utf8_bom_json_is_accepted(api):
    response = _post_raw(api, "﻿" + json.dumps(_payload()), "application/json")
    assert response.status_code == 201


@pytest.mark.parametrize("accept", ["application/json", "text/html", "application/xml", "*/*"])
def test_accept_header_does_not_break_json(api, accept):
    response = api.session.get(
        api.base_url + "/api/tickets", headers={"Accept": accept}, timeout=10
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.parametrize("method", ["OPTIONS", "HEAD", "PUT"])
def test_unsupported_methods(api, method):
    response = api.session.request(method, api.base_url + "/api/tickets", timeout=10)
    assert response.status_code in (405, 200)


def test_unknown_query_parameters_are_ignored(api):
    response = api.get("/api/tickets?unknown=1&limit=1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_trailing_slash_redirects(api):
    response = api.session.get(
        api.base_url + "/api/tickets/", allow_redirects=False, timeout=10
    )
    assert response.status_code in (307, 308)


def test_path_is_case_sensitive(api):
    assert api.get("/API/tickets").status_code == 404


def test_ticket_response_schema_is_stable(api):
    ticket = api.post("/api/tickets", json=_payload()).json()
    assert set(ticket) == {"id", "title", "description", "status", "priority", "created_at"}
    assert isinstance(ticket["id"], int)
    assert isinstance(ticket["title"], str)


def test_created_at_is_iso_datetime(api):
    ticket = api.post("/api/tickets", json=_payload()).json()
    datetime.fromisoformat(ticket["created_at"])


def test_health_schema_is_stable(api):
    body = api.get("/health").json()
    assert set(body) == {"status", "service", "version"}
    assert body["status"] == "ok"


def test_openapi_lists_ticket_endpoints(api):
    schema = api.get("/openapi.json").json()
    assert "/api/tickets" in schema["paths"]
    assert "post" in schema["paths"]["/api/tickets"]


def test_response_is_utf8_decodable(api):
    title = "中文兼容性😀"
    response = api.post("/api/tickets", json=_payload(title=title))
    assert title in response.content.decode("utf-8")


def test_max_description_round_trip(api):
    description = "d" * 5000
    response = api.post("/api/tickets", json=_payload(description=description))
    assert response.status_code == 201
    assert len(response.json()["description"]) == 5000


def test_unknown_field_is_ignored(api):
    body = _payload()
    body["future_field"] = {"nested": True}
    response = api.post("/api/tickets", json=body)
    assert response.status_code == 201
    assert "future_field" not in response.json()


def test_duplicate_json_keys_last_one_wins(api):
    raw = '{"title":"first","title":"second","priority":"low"}'
    response = _post_raw(api, raw, "application/json")
    assert response.status_code == 201
    assert response.json()["title"] == "second"


@pytest.mark.parametrize(
    "body",
    [
        [],
        [{"title": "array"}],
        "string-body",
        123,
    ],
)
def test_non_object_bodies_are_rejected(api, body):
    assert api.post("/api/tickets", json=body).status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "x", "description": None},
        {"title": "x", "priority": None},
        {"title": "x", "priority": 3},
    ],
)
def test_null_and_wrong_typed_optionals_are_rejected(api, payload):
    assert api.post("/api/tickets", json=payload).status_code == 422


def test_defaults_when_optional_fields_missing(api):
    response = api.post("/api/tickets", json={"title": "defaults only"})
    assert response.status_code == 201
    assert response.json()["priority"] == "medium"
    assert response.json()["description"] == ""


def test_oversized_id_is_rejected(api):
    response = api.get("/api/tickets/999999999999999999999999")
    assert response.status_code == 422


def test_negative_id_is_not_found(api):
    assert api.get("/api/tickets/-1").status_code == 404


def test_delete_returns_empty_204(api):
    ticket = api.post("/api/tickets", json=_payload()).json()
    response = api.delete(f"/api/tickets/{ticket['id']}")
    assert response.status_code == 204
    assert response.content == b""


def test_error_body_has_detail(api):
    response = api.get("/api/tickets/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "ticket not found"


def test_no_cors_headers_by_default(api):
    response = api.get("/api/tickets")
    assert "access-control-allow-origin" not in {key.lower() for key in response.headers}
