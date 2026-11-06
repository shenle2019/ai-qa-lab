"""Skills: run a stored UI case, and chat about a live page."""

from __future__ import annotations

import json
from typing import Any

from ... import llm_client
from ... import ui_models as models
from ..registry import Skill, SkillError, register
from ...ui_runner import RunError, execute_case, snapshot
from ...ui_steps import StepError, parse_env
from .llm_support import resolve_model

RUN_PROMPT_VERSION = "ui-run-v1"


def _run_case(payload: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    db = ctx.get("db")
    if db is None:
        raise SkillError("缺少数据库上下文", 500)
    case_id = payload.get("case_id")
    if not case_id:
        raise SkillError("需要 case_id")
    case = db.get(models.UiCase, int(case_id))
    if case is None:
        raise SkillError("用例不存在", 404)

    run = models.UiRun(
        project_id=case.project_id,
        case_id=case.id,
        title=case.title,
        status="running",
        duration_ms=0,
        steps_json="[]",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        result = execute_case(case, run_id=run.id, headless=bool(payload.get("headless", True)))
    except RunError as exc:
        run.status = "failed"
        run.error = str(exc)
        db.commit()
        raise SkillError(str(exc), 503) from exc

    run.status = "passed" if not result["error"] else "failed"
    run.steps_json = json.dumps(result["steps"], ensure_ascii=False)
    run.duration_ms = result["duration_ms"]
    run.screenshot = result["screenshot"]
    run.error = result["error"]
    db.commit()
    db.refresh(run)

    return {
        "run_id": run.id,
        "case_id": case.id,
        "status": run.status,
        "duration_ms": run.duration_ms,
        "steps": result["steps"],
        "screenshot": run.screenshot,
        "error": run.error,
    }


def _run_chat(payload: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    db = ctx.get("db")
    if db is None:
        raise SkillError("缺少数据库上下文", 500)
    url = str(payload.get("url") or "").strip()
    question = str(payload.get("question") or "").strip()
    if not url or not question:
        raise SkillError("需要 url 和 question")
    try:
        env = parse_env(payload.get("env") or {})
    except StepError as exc:
        raise SkillError(str(exc)) from exc

    config = resolve_model(db, payload.get("model_id"))
    try:
        page = snapshot(url, env=env)
    except RunError as exc:
        raise SkillError(str(exc), 503) from exc
    except Exception as exc:  # noqa: BLE001
        raise SkillError(f"打开页面失败：{exc}", 502) from exc

    context = (
        f"页面地址：{page['url']}\n页面标题：{page['title']}\n\n"
        f"页面文字：\n{page['text'][:2500]}"
    )
    reply = llm_client.chat_text(
        db,
        config,
        [
            {
                "role": "system",
                "content": (
                    "你是测试工程师的页面助手。根据给出的页面内容回答用户问题，"
                    "只讲页面上能看到的东西，不确定就直说；回答控制在 200 字以内。"
                ),
            },
            {"role": "user", "content": f"{context}\n\n问题：{question}"},
        ],
        purpose="ui_chat",
        prompt_version=RUN_PROMPT_VERSION,
        timeout=90.0,
        max_tokens=1200,
    )
    return {"reply": reply, "title": page["title"], "url": page["url"], "model_name": config.model_name}


register(
    Skill(
        id="ui.run",
        name="UI 用例执行",
        category="ui",
        description="用 Playwright 执行一条 UI 用例，逐步记录结果，失败时截图。",
        input_schema={
            "type": "object",
            "required": ["case_id"],
            "properties": {"case_id": {"type": "integer"}, "headless": {"type": "boolean"}},
        },
        output_schema={"type": "object"},
        handler=_run_case,
    )
)

register(
    Skill(
        id="ui.chat",
        name="页面自由对话",
        category="ui",
        description="抓取页面快照后由大模型回答关于这个页面的问题。",
        input_schema={
            "type": "object",
            "required": ["url", "question"],
            "properties": {
                "url": {"type": "string"},
                "question": {"type": "string"},
                "env": {"type": "object"},
                "model_id": {"type": "integer"},
            },
        },
        output_schema={"type": "object"},
        handler=_run_chat,
    )
)
