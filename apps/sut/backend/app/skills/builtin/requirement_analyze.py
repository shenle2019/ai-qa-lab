"""Builtin skill: analyse a requirement into features / UI / open questions."""

from __future__ import annotations

import json

from ..registry import Skill, SkillError, register
from ... import llm_client, requirement_models
from .llm_support import require_db, resolve_model

PROMPT_VERSION = "req-analysis-v1"

SYSTEM_PROMPT = """你是资深测试分析师。阅读用户给出的需求材料，拆解成可测试的结构化信息。

只输出一个 JSON 对象，不要输出解释文字，结构如下：
{
  "summary": "两三句话概括这个需求要做什么",
  "features": [
    {"name": "功能点名称", "description": "具体行为", "priority": "high|medium|low", "acceptance": "验收标准，可验证的一句话"}
  ],
  "ui": [
    {"page": "页面或入口名称", "description": "页面职责与关键交互", "elements": ["关键元素1", "关键元素2"]}
  ],
  "clarifications": [
    {"question": "需要向产品/开发澄清的问题", "why": "不澄清会带来的测试风险"}
  ],
  "risks": ["测试风险或容易被忽略的边界"]
}

要求：
1. features 覆盖主流程、异常流程、权限与边界，不要只写正常路径。
2. 需求没写清楚的地方放进 clarifications，不要自己编造业务规则。
3. 全部使用简体中文。
"""


def _normalise(raw: dict) -> dict:
    def as_list(value):
        return value if isinstance(value, list) else []

    features = []
    for item in as_list(raw.get("features")):
        if not isinstance(item, dict):
            continue
        priority = str(item.get("priority") or "medium").lower()
        if priority not in {"high", "medium", "low"}:
            priority = "medium"
        features.append(
            {
                "name": str(item.get("name") or "").strip(),
                "description": str(item.get("description") or "").strip(),
                "priority": priority,
                "acceptance": str(item.get("acceptance") or "").strip(),
            }
        )

    ui = []
    for item in as_list(raw.get("ui")):
        if not isinstance(item, dict):
            continue
        ui.append(
            {
                "page": str(item.get("page") or "").strip(),
                "description": str(item.get("description") or "").strip(),
                "elements": [str(e).strip() for e in as_list(item.get("elements")) if str(e).strip()],
            }
        )

    clarifications = []
    for item in as_list(raw.get("clarifications")):
        if isinstance(item, dict):
            clarifications.append(
                {
                    "question": str(item.get("question") or "").strip(),
                    "why": str(item.get("why") or "").strip(),
                }
            )
        elif isinstance(item, str) and item.strip():
            clarifications.append({"question": item.strip(), "why": ""})

    return {
        "summary": str(raw.get("summary") or "").strip(),
        "features": [f for f in features if f["name"]],
        "ui": [u for u in ui if u["page"]],
        "clarifications": [c for c in clarifications if c["question"]],
        "risks": [str(r).strip() for r in as_list(raw.get("risks")) if str(r).strip()],
    }


def requirement_text(req: requirement_models.Requirement, attachments) -> str:
    """Requirement body plus any attachment text we managed to extract."""
    parts = [req.body.strip()]
    for item in attachments:
        if item.extracted_text:
            parts.append(f"【附件 {item.filename}】\n{item.extracted_text}")
    return "\n\n".join(part for part in parts if part).strip()


def _run(payload, ctx):
    db = require_db(ctx)
    requirement_id = payload.get("requirement_id")
    if not requirement_id:
        raise SkillError("requirement_id 不能为空")
    req = db.get(requirement_models.Requirement, int(requirement_id))
    if req is None:
        raise SkillError("requirement not found", status_code=404)

    text = str(payload.get("text") or "").strip()
    if not text:
        attachments = (
            db.query(requirement_models.RequirementAttachment)
            .filter(requirement_models.RequirementAttachment.requirement_id == req.id)
            .all()
        )
        text = requirement_text(req, attachments)
    if not text:
        raise SkillError("需求正文为空，请先填写正文或上传可解析的附件")

    config = resolve_model(db, payload.get("model_id"))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"需求标题：{req.title}\n\n需求材料：\n{text[:20000]}"},
    ]
    try:
        raw = llm_client.chat_json(
            db,
            config,
            messages,
            purpose="requirement_analysis",
            prompt_version=PROMPT_VERSION,
            timeout=120.0,
            max_tokens=6000,
        )
    except llm_client.LLMError as exc:
        raise SkillError(str(exc), status_code=502) from exc

    analysis = _normalise(raw)
    req.analysis_json = json.dumps(analysis, ensure_ascii=False)
    if req.status == "draft":
        req.status = "analyzed"
    db.commit()

    return {
        "requirement_id": req.id,
        "model_name": config.model_name,
        "prompt_version": PROMPT_VERSION,
        "analysis": analysis,
    }


SKILL = register(
    Skill(
        id="requirement.analyze",
        name="需求分析",
        category="requirement",
        description="读取需求正文与附件，输出功能清单、界面描述、待澄清项与测试风险。",
        input_schema={
            "type": "object",
            "required": ["requirement_id"],
            "properties": {
                "requirement_id": {"type": "integer"},
                "text": {"type": "string", "description": "覆盖默认正文（可选）"},
                "model_id": {"type": "integer"},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "analysis": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "features": {"type": "array"},
                        "ui": {"type": "array"},
                        "clarifications": {"type": "array"},
                        "risks": {"type": "array"},
                    },
                }
            },
        },
        handler=_run,
    )
)
