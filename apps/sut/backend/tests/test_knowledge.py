"""Knowledge base: chunking, CRUD, retrieval and the registered skills."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE = """# 工单系统接口说明

## 列表接口
GET /api/tickets 返回工单列表，支持 status、page、page_size 三个查询参数。
返回结构是 {items: [], total: 0}，其中 total 表示满足条件的总数。

## 导出接口
GET /api/tickets/export 导出当前筛选结果为 CSV，文件使用 UTF-8 BOM 编码。
当筛选结果超过 5000 条时，接口返回 202 并转到后台任务，完成后站内信通知。

## 删除接口
DELETE /api/tickets/{id} 删除单条工单，成功返回 204，工单不存在返回 404。

## 权限
所有写接口都需要 Bearer 访问密钥，匿名请求返回 401。
"""


def _make_kb(name: str = "工单接口知识库", chunk_size: int = 200, chunk_overlap: int = 40) -> dict:
    response = client.post(
        "/api/platform/knowledge-bases",
        json={"name": name, "description": "接口文档", "chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_list_knowledge_base():
    created = _make_kb("接口文档库 A")
    assert created["chunk_size"] == 200
    listed = client.get("/api/platform/knowledge-bases").json()
    assert any(item["id"] == created["id"] for item in listed)


def test_duplicate_name_rejected():
    _make_kb("接口文档库 B")
    again = client.post("/api/platform/knowledge-bases", json={"name": "接口文档库 B"})
    assert again.status_code == 409


def test_create_requires_name():
    response = client.post("/api/platform/knowledge-bases", json={"name": ""})
    assert response.status_code == 422


def test_add_text_document_chunks_and_lists():
    kb = _make_kb("接口文档库 C")
    response = client.post(
        f"/api/platform/knowledge-bases/{kb['id']}/documents/text",
        json={"filename": "tickets.md", "text": SAMPLE},
    )
    assert response.status_code == 201, response.text
    document = response.json()
    assert document["chunk_count"] >= 2
    assert document["char_count"] == len(SAMPLE.strip())

    chunks = client.get(f"/api/platform/knowledge-documents/{document['id']}/chunks").json()
    assert len(chunks) == document["chunk_count"]
    assert chunks[0]["seq"] == 0
    assert all(chunk["char_count"] <= kb["chunk_size"] + 1 for chunk in chunks)

    refreshed = client.get(f"/api/platform/knowledge-bases/{kb['id']}").json()
    assert refreshed["document_count"] == 1
    assert refreshed["chunk_count"] == document["chunk_count"]


def test_upload_document_extracts_text():
    kb = _make_kb("接口文档库 D")
    response = client.post(
        f"/api/platform/knowledge-bases/{kb['id']}/documents",
        files={"file": ("tickets.md", SAMPLE.encode("utf-8"), "text/markdown")},
    )
    assert response.status_code == 201, response.text
    assert response.json()["source"] == "upload"


def test_upload_without_text_rejected():
    kb = _make_kb("接口文档库 E")
    response = client.post(
        f"/api/platform/knowledge-bases/{kb['id']}/documents",
        files={"file": ("empty.bin", b"\x00\x01\x02", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_search_returns_ranked_hits():
    kb = _make_kb("接口文档库 F")
    client.post(
        f"/api/platform/knowledge-bases/{kb['id']}/documents/text",
        json={"filename": "tickets.md", "text": SAMPLE},
    )
    response = client.post(
        f"/api/platform/knowledge-bases/{kb['id']}/search",
        json={"query": "导出接口超过 5000 条会怎样", "top_k": 3},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["hits"], "expected at least one hit"
    assert body["hits"][0]["filename"] == "tickets.md"
    assert "5000" in body["hits"][0]["snippet"]
    assert body["took_ms"] >= 0


def test_search_on_empty_base_returns_nothing():
    kb = _make_kb("接口文档库 G")
    body = client.post(
        f"/api/platform/knowledge-bases/{kb['id']}/search", json={"query": "随便问问"}
    ).json()
    assert body["hits"] == []


def test_delete_document_and_base():
    kb = _make_kb("接口文档库 H")
    created = client.post(
        f"/api/platform/knowledge-bases/{kb['id']}/documents/text",
        json={"filename": "a.txt", "text": SAMPLE},
    ).json()
    assert client.delete(f"/api/platform/knowledge-documents/{created['id']}").status_code == 204
    assert client.get(f"/api/platform/knowledge-bases/{kb['id']}").json()["chunk_count"] == 0
    assert client.delete(f"/api/platform/knowledge-bases/{kb['id']}").status_code == 204
    assert client.get(f"/api/platform/knowledge-bases/{kb['id']}").status_code == 404


def test_knowledge_skills_registered_and_runnable():
    skills = client.get("/api/platform/skills", params={"category": "knowledge"}).json()
    ids = {item["id"] for item in skills}
    assert {"kb.create", "kb.list", "kb.search", "kb.document.add"} <= ids

    created = client.post(
        "/api/platform/skills/kb.create/run", json={"name": "技能建的知识库"}
    )
    assert created.status_code == 200, created.text
    kb_id = created.json()["result"]["kb"]["id"]

    added = client.post(
        "/api/platform/skills/kb.document.add/run",
        json={"kb_id": kb_id, "filename": "s.txt", "text": SAMPLE},
    )
    assert added.status_code == 200, added.text
    assert added.json()["result"]["document"]["chunk_count"] >= 1

    hits = client.post(
        "/api/platform/skills/kb.search/run", json={"kb_id": kb_id, "query": "权限 401"}
    )
    assert hits.status_code == 200, hits.text
    body = hits.json()["result"]
    assert body["total"] >= 1
    assert "context" in body


def test_search_skill_validates_payload():
    missing = client.post("/api/platform/skills/kb.search/run", json={"kb_id": 1, "query": ""})
    assert missing.status_code == 400
    unknown = client.post("/api/platform/skills/kb.search/run", json={"kb_id": 99999, "query": "x"})
    assert unknown.status_code == 404
