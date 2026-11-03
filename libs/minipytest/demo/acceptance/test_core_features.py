from uuid import uuid4

from libs.minipytest import assert_that, mark, parametrize, raises

FUNCTION_SEEN: list[int] = []


def test_assertion_api():
    assert_that({"status": "ok"}).contains("status")
    assert_that([1, 2, 3]).has_length(3)
    assert_that("ai-qa-lab").matches("qa")


def test_raises_context():
    with raises(ValueError, match="boom") as ctx:
        raise ValueError("boom happened")
    assert_that(str(ctx.value)).contains("boom")


def test_session_fixture_shared_a(session_value):
    session_value["count"] += 1
    assert_that(session_value["count"]).is_equal_to(1)


def test_session_fixture_shared_b(session_value):
    assert_that(session_value["count"]).is_equal_to(1)


def test_module_fixture_shared_a(module_value):
    module_value["count"] += 1
    assert_that(module_value["count"]).is_equal_to(1)


def test_module_fixture_shared_b(module_value):
    assert_that(module_value["count"]).is_equal_to(1)


def test_function_fixture_a(function_value):
    FUNCTION_SEEN.append(function_value)
    assert_that(function_value).is_greater_than(0)


def test_function_fixture_b(function_value):
    assert_that(function_value).is_not_equal_to(FUNCTION_SEEN[0])


def test_autouse_ran(state):
    assert_that(state["autouse"]).is_true()


@parametrize("role", ["admin", "viewer"])
@parametrize("status", ["open", "closed"])
def test_permission_matrix(role, status):
    assert_that(role).is_in(["admin", "viewer"])
    assert_that(status).is_in(["open", "closed"])


@mark.skip("demo: skip marker")
def test_skip_demo():
    raise AssertionError("this should not run")


@mark.xfail("demo: expected failure")
def test_xfail_demo():
    assert_that(1).is_equal_to(2)


@mark.xfail("demo: expected pass")
def test_xpass_demo():
    assert_that(1).is_equal_to(1)


ATTEMPTS = {"n": 0}


@mark.retry(2)
def test_retry_flaky():
    ATTEMPTS["n"] += 1
    assert_that(ATTEMPTS["n"]).is_greater_or_equal_to(2)


@mark.smoke
def test_health(api):
    base_url, client = api
    response = client.get(f"{base_url}/health", timeout=10)
    assert_that(response.status_code).is_equal_to(200)
    assert_that(response.json()["status"]).is_equal_to("ok")


def test_create_and_get_ticket(api):
    base_url, client = api
    title = f"minipytest ticket {uuid4().hex[:8]}"
    created = client.post(
        f"{base_url}/api/tickets",
        json={"title": title, "description": "created by minipytest", "priority": "high"},
        timeout=10,
    )
    assert_that(created.status_code).is_equal_to(201)
    ticket_id = created.json()["id"]
    fetched = client.get(f"{base_url}/api/tickets/{ticket_id}", timeout=10)
    assert_that(fetched.status_code).is_equal_to(200)
    assert_that(fetched.json()["title"]).is_equal_to(title)
    assert_that(fetched.json()["priority"]).is_equal_to("high")


def test_kb_query(api):
    base_url, client = api
    response = client.post(
        f"{base_url}/api/kb/query",
        json={"question": "minipytest 怎么用", "top_k": 3},
        timeout=10,
    )
    assert_that(response.status_code).is_equal_to(200)
    payload = response.json()
    assert_that(payload["top_k"]).is_equal_to(3)
    assert_that(payload["answer"]).contains("minipytest")
