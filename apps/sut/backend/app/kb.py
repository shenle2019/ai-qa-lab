"""Lexical retrieval over tickets and a small built-in knowledge base.

This is intentionally simple (token overlap, no embeddings) but returns real
sources instead of a hard-coded mock answer.
"""

import re

from sqlalchemy.orm import Session

from . import models

FAQ = [
    {
        "title": "工单优先级怎么划分",
        "text": "工单优先级分为低、中、高。高优先级用于影响核心流程的故障，需要在当天响应；中优先级按迭代处理；低优先级排入常规队列。",
        "source": "faq:priority",
    },
    {
        "title": "如何升级工单优先级",
        "text": "在工单列表中找到目标工单，修改优先级下拉框为高，或在接口 PATCH /api/tickets/{id} 中传 priority=high。",
        "source": "faq:priority-change",
    },
    {
        "title": "如何关闭工单",
        "text": "把工单状态改为 closed，或在接口 PATCH /api/tickets/{id} 中传 status=closed。关闭后仍可通过接口重新打开。",
        "source": "faq:close",
    },
    {
        "title": "登录验证码不显示",
        "text": "优先检查浏览器是否拦截了验证码脚本，再确认后端验证码接口返回 200 且响应包含图片。Chrome 下需要允许第三方 Cookie。",
        "source": "faq:captcha",
    },
    {
        "title": "知识库回答超时",
        "text": "检查检索服务耗时与模型调用耗时。接口超时阈值是 30 秒，超时后应返回可读错误而不是挂起连接。",
        "source": "faq:kb-timeout",
    },
    {
        "title": "导出报表字段缺失",
        "text": "导出 CSV 需要包含创建时间、状态、优先级和标题。字段缺失通常是查询投影漏了列，检查导出 SQL 的 select 列表。",
        "source": "faq:export",
    },
    {
        "title": "移动端布局横向滚动",
        "text": "检查是否有固定宽度容器或未换行的长文本。给表格加 overflow-x:auto，并确认 viewport meta 正确。",
        "source": "faq:mobile",
    },
    {
        "title": "权限校验绕过",
        "text": "所有写接口应在服务端校验身份，不能只依赖前端隐藏按钮。生产环境要求 Bearer 访问密钥，匿名写请求返回 401。",
        "source": "faq:auth",
    },
]

WORD_PATTERN = re.compile(r"[a-zA-Z0-9]+")
CJK_PATTERN = re.compile(r"[一-鿿]+")


def _tokens(text: str) -> set[str]:
    lowered = (text or "").lower()
    tokens = set(WORD_PATTERN.findall(lowered))
    for chunk in CJK_PATTERN.findall(lowered):
        if len(chunk) == 1:
            tokens.add(chunk)
            continue
        tokens.update(chunk[index : index + 2] for index in range(len(chunk) - 1))
    return tokens


def _snippet(text: str, limit: int = 140) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + "…"


def search(db: Session, question: str, top_k: int) -> list[dict]:
    query_tokens = _tokens(question)
    if not query_tokens:
        return []

    documents = list(FAQ)
    for ticket in db.query(models.Ticket).order_by(models.Ticket.id.desc()).limit(200).all():
        documents.append(
            {
                "title": ticket.title,
                "text": f"{ticket.title} {ticket.description}",
                "source": f"ticket#{ticket.id}",
            }
        )

    ranked = []
    for document in documents:
        overlap = len(query_tokens & _tokens(document["text"] + " " + document["title"]))
        if question and question.strip() in document["text"]:
            overlap += 10
        if overlap:
            ranked.append((overlap, document))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "title": document["title"],
            "snippet": _snippet(document["text"]),
            "source": document["source"],
            "score": score,
        }
        for score, document in ranked[:top_k]
    ]


def answer(question: str, matches: list[dict]) -> str:
    if not matches:
        return f"没有在工单和内置知识中找到与“{question}”相关的记录。"
    lines = [f"关于“{question}”，找到 {len(matches)} 条相关记录："]
    for index, item in enumerate(matches, start=1):
        lines.append(f"{index}. {item['title']}：{item['snippet']}（{item['source']}）")
    return "\n".join(lines)
