"""Builtin skill: turn a requirement into draft test cases (AI generation)."""

from __future__ import annotations

import json

from ..registry import Skill, SkillError, register
from ... import case_generator, llm_client, llm_models
from ... import platform_models as models
from ... import requirement_models


def _resolve_model(db, model_id):
    if model_id is not None:
        config = db.get(llm_models.ModelConfig, model_id)
        if config is None:
            raise SkillError("model not found", status_code=404)
        return config
    config = (
        db.query(llm_models.ModelConfig)
        .filter(llm_models.ModelConfig.enabled.is_(True))
        .order_by(llm_models.ModelConfig.id)
        .first()
    )
    if config is None or not config.enabled:
        raise SkillError("没有启用的模型，请先在模型中心配置")
    return config


def _requirement_text(db, requirement_id):
    """Build the generation prompt from a stored requirement plus its analysis."""
    req = db.get(requirement_models.Requirement, int(requirement_id))
    if req is None:
        raise SkillError("requirement not found", status_code=404)
    parts = [req.body.strip() or req.title]
    analysis = json.loads(req.analysis_json) if req.analysis_json else None
    features = (analysis or {}).get("features") or []
    if features:
        lines = ["已识别的功能点（请覆盖）："]
        for item in features:
            name = str(item.get("name") or "").strip()
            acceptance = str(item.get("acceptance") or "").strip()
            description = str(item.get("description") or "").strip()
            detail = acceptance or description
            lines.append(f"- {name}" + (f"：{detail}" if detail else ""))
        parts.append("\n".join(lines))
    return {"text": "\n\n".join(parts), "project_id": req.project_id, "requirement": req}


def _run(payload, ctx):
    db = ctx.get("db")
    if db is None:
        raise SkillError("db session missing")

    requirement = str(payload.get("requirement") or "").strip()
    requirement_id = payload.get("requirement_id")
    project_id = payload.get("project_id")

    if requirement_id is not None:
        built = _requirement_text(db, requirement_id)
        if not requirement:
            requirement = built["text"]
        project_id = project_id or built["project_id"]
    if not requirement:
        raise SkillError("requirement 不能为空")

    project = db.get(models.Project, project_id) if project_id else None
    if project is None:
        raise SkillError("project not found", status_code=404)
    max_cases = int(payload.get("max_cases") or 10)
    max_cases = max(1, min(max_cases, 50))
    config = _resolve_model(db, payload.get("model_id"))
    try:
        items = case_generator.generate(db, config, requirement, max_cases)
    except llm_client.LLMError as exc:
        raise SkillError(str(exc), status_code=502) from exc

    created = []
    for item in items:
        case = models.TestCase(
            project_id=project.id,
            title=item["title"],
            module=item["module"],
            priority=item["priority"],
            steps=case_generator.steps_to_text(item["steps"]),
            expected=item["expected"],
            status="draft",
            source="ai",
            prompt_version=case_generator.PROMPT_VERSION,
            steps_json=case_generator.steps_to_json(item["steps"]),
        )
        db.add(case)
        created.append(case)
    db.commit()
    for case in created:
        db.refresh(case)
    return {
        "model_name": config.model_name,
        "prompt_version": case_generator.PROMPT_VERSION,
        "cases": [
            {
                "id": c.id,
                "project_id": c.project_id,
                "title": c.title,
                "module": c.module,
                "priority": c.priority,
                "steps": c.steps,
                "expected": c.expected,
                "status": c.status,
                "source": c.source,
            }
            for c in created
        ],
    }


SKILL = register(
    Skill(
        id="case.generate",
        name="AI 生成用例",
        category="case",
        description="输入需求文本，调用已启用的大模型生成测试用例草稿（draft），由用户决定是否写入用例管理。",
        input_schema={
            "type": "object",
            "required": ["project_id", "requirement"],
            "properties": {
                "project_id": {"type": "integer"},
                "requirement": {"type": "string"},
                "max_cases": {"type": "integer", "default": 10},
                "model_id": {"type": "integer"},
            },
        },
        output_schema={"type": "object"},
        handler=_run,
    )
)
