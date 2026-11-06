"""Builtin skill: retrieve chunks from a knowledge base."""

from __future__ import annotations

from ..registry import Skill, SkillError, register
from ... import knowledge_models as models
from ...knowledge_search import search as run_search


def _run(payload, ctx):
    db = ctx.get("db")
    if db is None:
        raise SkillError("db session missing")
    kb_id = payload.get("kb_id")
    query = str(payload.get("query") or "").strip()
    if not kb_id:
        raise SkillError("kb_id 不能为空")
    if not query:
        raise SkillError("检索内容不能为空")
    if not db.get(models.KnowledgeBase, int(kb_id)):
        raise SkillError("知识库不存在", 404)
    top_k = int(payload.get("top_k") or 5)
    hits = run_search(db, int(kb_id), query, top_k)
    return {
        "kb_id": int(kb_id),
        "query": query,
        "total": len(hits),
        "hits": [
            {
                "chunk_id": hit["chunk_id"],
                "document_id": hit["document_id"],
                "filename": hit["filename"],
                "seq": hit["seq"],
                "score": hit["score"],
                "snippet": hit["snippet"],
            }
            for hit in hits
        ],
        "context": "\n\n".join(f"[{hit['filename']}#{hit['seq']}] {hit['snippet']}" for hit in hits),
    }


SKILL = register(
    Skill(
        id="kb.search",
        name="知识库检索",
        category="knowledge",
        description="在指定知识库里检索相关分块，返回命中片段与可直接拼进 prompt 的 context。",
        input_schema={
            "type": "object",
            "properties": {
                "kb_id": {"type": "integer"},
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["kb_id", "query"],
        },
        output_schema={"type": "object"},
        handler=_run,
    )
)
