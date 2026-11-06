"""Phase 3 smoke: create a library, ingest real files, retrieve, clean up."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "phases" / "phase-3" / "smoke-output.json"
SOURCE = ROOT / "docs" / "requirements" / "2026-11-06-ai-test-platform-refactor.md"


def main() -> int:
    report: dict = {"base": BASE, "source": str(SOURCE), "steps": []}
    with httpx.Client(base_url=BASE, timeout=120.0) as client:
        report["health"] = client.get("/health").json()

        existing = client.get("/api/platform/knowledge-bases").json()
        for item in existing:
            if item["name"] == "平台重构方案库":
                client.delete(f"/api/platform/knowledge-bases/{item['id']}")

        created = client.post(
            "/api/platform/knowledge-bases",
            json={
                "name": "平台重构方案库",
                "description": "AI 测试平台重构方案与阶段文档",
                "chunk_size": 500,
                "chunk_overlap": 80,
            },
        )
        created.raise_for_status()
        kb = created.json()
        report["kb"] = {"id": kb["id"], "name": kb["name"], "chunk_size": kb["chunk_size"]}

        with SOURCE.open("rb") as handle:
            uploaded = client.post(
                f"/api/platform/knowledge-bases/{kb['id']}/documents",
                files={"file": (SOURCE.name, handle, "text/markdown")},
            )
        uploaded.raise_for_status()
        document = uploaded.json()
        report["upload"] = {
            "id": document["id"],
            "filename": document["filename"],
            "char_count": document["char_count"],
            "chunk_count": document["chunk_count"],
            "note": document["note"],
        }

        pasted = client.post(
            f"/api/platform/knowledge-bases/{kb['id']}/documents/text",
            json={
                "filename": "接口约定.md",
                "text": (
                    "工单导出接口 GET /api/tickets/export 返回 CSV，编码 UTF-8 BOM。\n\n"
                    "导出条数超过 5000 条时接口返回 202，转为后台任务，完成后站内信通知。\n\n"
                    "所有写接口需要 Bearer 访问密钥，匿名请求返回 401。"
                ),
            },
        )
        pasted.raise_for_status()
        report["paste"] = pasted.json()["chunk_count"]

        chunks = client.get(f"/api/platform/knowledge-documents/{document['id']}/chunks?limit=3").json()
        report["chunk_sample"] = [{"seq": c["seq"], "chars": c["char_count"]} for c in chunks]

        search = client.post(
            f"/api/platform/knowledge-bases/{kb['id']}/search",
            json={"query": "导出超过 5000 条怎么处理", "top_k": 3},
        )
        search.raise_for_status()
        body = search.json()
        report["search"] = {
            "took_ms": body["took_ms"],
            "hits": [
                {"filename": hit["filename"], "seq": hit["seq"], "score": hit["score"]}
                for hit in body["hits"]
            ],
            "top_snippet": body["hits"][0]["snippet"] if body["hits"] else None,
        }

        skill = client.post(
            "/api/platform/skills/kb.search/run",
            json={"kb_id": kb["id"], "query": "匿名请求返回什么", "top_k": 2},
        )
        skill.raise_for_status()
        report["skill_search"] = {
            "total": skill.json()["result"]["total"],
            "context_head": skill.json()["result"]["context"][:160],
        }

        summary = client.get(f"/api/platform/knowledge-bases/{kb['id']}").json()
        report["counts"] = {
            "documents": summary["document_count"],
            "chunks": summary["chunk_count"],
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
