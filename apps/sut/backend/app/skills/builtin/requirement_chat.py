"""Builtin skill: the right-hand requirement chat agent.

The agent answers questions about the requirement and, when the user asks for a
change, may return an updated analysis inside a ```json fenced block. We pick
that block up and persist it, so "跟它说一句就改分析" actually works.
"""

from __future__ import annotations

import json
import re

from ..registry import Skill, SkillError, register
from ... import llm_client, requirement_models
from .llm_support import require_db, resolve_model

PROMPT_VERSION = "req-chat-v1"
HISTORY_LIMIT = 12

SYSTEM_PROMPT = """你是测试团队的需求助手，正在和测试同学一起梳理一条需求。

你可以：
1. 解答关于这条需求的疑问，指出需要澄清的点。
2. 在用户要求修改分析结果时，输出一份完整的新分析。

当前需求的材料与分析结果会提供给你。回答要具体、可执行，不要客套话，不要重复用户已经知道的内容。

如果用户要求你修改分析结果，请在回答末尾追加一个 ```json 代码块，内容是完整的分析对象：
{"summary": "...", "features": [...], "ui": [...], "clarifications": [...], "risks": [...]}
只修改与分析相关的部分，其余字段原样保留。不涉及修改时不要输出这个代码块。
"""


def _extract_analysis(reply: str) -> dict | None:
    """Pull a ```json block that looks like a full analysis out of the reply."""
    for block in re.findall(r"```json\s*(.*?)```", reply, re.S):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and isinstance(data.get("features"), list):
            return data
    return None


def _run(payload, ctx):
    db = require_db(ctx)
    requirement_id = payload.get("requirement_id")
    message = str(payload.get("message") or "").strip()
    if not requirement_id:
        raise SkillError("requirement_id 不能为空")
    if not message:
        raise SkillError("message 不能为空")

    req = db.get(requirement_models.Requirement, int(requirement_id))
    if req is None:
        raise SkillError("requirement not found", status_code=404)

    history = (
        db.query(requirement_models.RequirementMessage)
        .filter(requirement_models.RequirementMessage.requirement_id == req.id)
        .order_by(requirement_models.RequirementMessage.id.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    history.reverse()

    analysis = {}
    if req.analysis_json:
        try:
            analysis = json.loads(req.analysis_json)
        except json.JSONDecodeError:
            analysis = {}

    context = json.dumps(
        {
            "title": req.title,
            "body": req.body[:8000],
            "analysis": analysis,
        },
        ensure_ascii=False,
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "system", "content": f"当前需求上下文：\n{context}"})
    for item in history:
        role = "assistant" if item.role == "assistant" else "user"
        messages.append({"role": role, "content": item.content})
    messages.append({"role": "user", "content": message})

    config = resolve_model(db, payload.get("model_id"))
    try:
        reply = llm_client.chat_text(
            db,
            config,
            messages,
            purpose="requirement_chat",
            prompt_version=PROMPT_VERSION,
            timeout=90.0,
            max_tokens=3000,
            temperature=0.4,
        )
    except llm_client.LLMError as exc:
        raise SkillError(str(exc), status_code=502) from exc

    updated_analysis = _extract_analysis(reply)
    if updated_analysis is not None:
        req.analysis_json = json.dumps(updated_analysis, ensure_ascii=False)

    # Keep the JSON payload out of the transcript: it is a machine hand-off, not
    # something a tester wants to read in the chat log.
    clean_reply = re.sub(r"```json\s*.*?```", "", reply, flags=re.S).strip()
    if updated_analysis is not None and not clean_reply:
        clean_reply = "已根据你的要求更新分析结果。"
    elif updated_analysis is not None:
        clean_reply = f"{clean_reply}\n\n（分析结果已更新）"

    db.add(requirement_models.RequirementMessage(requirement_id=req.id, role="user", content=message))
    db.add(
        requirement_models.RequirementMessage(
            requirement_id=req.id, role="assistant", content=clean_reply
        )
    )
    db.commit()

    return {
        "requirement_id": req.id,
        "reply": clean_reply,
        "model_name": config.model_name,
        "prompt_version": PROMPT_VERSION,
        "analysis_updated": updated_analysis is not None,
        "analysis": updated_analysis,
    }


SKILL = register(
    Skill(
        id="requirement.chat",
        name="需求对话助手",
        category="requirement",
        description="围绕一条需求对话：答疑、补充澄清点，并可按对话内容更新分析结果。",
        input_schema={
            "type": "object",
            "required": ["requirement_id", "message"],
            "properties": {
                "requirement_id": {"type": "integer"},
                "message": {"type": "string"},
                "model_id": {"type": "integer"},
            },
        },
        output_schema={"type": "object"},
        handler=_run,
    )
)
