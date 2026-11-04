import pytest


def test_kb_query_returns_sources(api):
    question = "工单如何升级优先级？"

    response = api.post(
        "/api/kb/query",
        json={"question": question, "top_k": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert question in body["answer"]
    assert body["top_k"] == 2
    assert body["sources"]
    assert any("优先级" in item["title"] for item in body["sources"])


def test_kb_query_unknown_question_has_no_sources(api):
    response = api.post("/api/kb/query", json={"question": "完全不相关的火星天气"})
    body = response.json()
    assert response.status_code == 200
    assert body["sources"] == []
    assert "没有" in body["answer"]


def test_kb_query_default_top_k(api):
    response = api.post("/api/kb/query", json={"question": "如何关闭工单？"})

    assert response.status_code == 200
    assert response.json()["top_k"] == 3


def test_kb_query_empty_question_returns_422(api):
    response = api.post("/api/kb/query", json={"question": ""})

    assert response.status_code == 422


def test_kb_query_missing_question_returns_422(api):
    response = api.post("/api/kb/query", json={})

    assert response.status_code == 422


@pytest.mark.parametrize("top_k", [0, 11])
def test_kb_query_top_k_out_of_range_returns_422(api, top_k):
    response = api.post(
        "/api/kb/query",
        json={"question": "越界测试", "top_k": top_k},
    )

    assert response.status_code == 422
