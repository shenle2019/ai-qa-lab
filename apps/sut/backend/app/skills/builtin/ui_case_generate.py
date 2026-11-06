"""Skill: turn a live page snapshot into runnable UI steps."""

from __future__ import annotations

import json
from typing import Any

from ... import llm_client
from ... import ui_models as models
from ..registry import Skill, SkillError, register
from ...ui_runner import RunError, snapshot
from ...ui_steps import StepError, normalise_steps, parse_env
from .llm_support import resolve_model

PROMPT_VERSION = "ui-case-v1"

SYSTEM_PROMPT = """你是资深 Web UI 自动化工程师。用户给出一个页面的文字快照和一条测试目标，
你要输出可以直接执行的 Playwright 步骤。

只输出 JSON：
{
  "reasoning": "一句话说明你怎么定位元素",
  "steps": [
    {"action": "goto", "value": "http://..."},
    {"action": "fill", "target": "input[placeholder=搜索名称或路径]", "value": "工单"},
    {"action": "click", "target": "text=查询"},
    {"action": "assert_text", "target": "body", "value": "共 1 条"}
  ]
}

规则：
1. action 只能是 goto / click / fill / press / select / hover / wait / assert_text / assert_visible / assert_url / screenshot。
2. target 优先用稳定的属性选择器（input[placeholder=...]、button[type=submit]、#id），
   没有稳定属性时用 Playwright 的 text=文字 语法。
3. 每个用例 3~10 步，最后至少一步断言；断言写页面真实出现过的文字。
4. 不要写需要登录才能到达的步骤；如果目标需要登录，直接用页面里已有的入口。
5. 不要编造按钮，只能使用快照里出现过的元素。"""


def _nodes_text(nodes: list[dict[str, Any]]) -> str:
    lines = []
    for item in nodes[:60]:
        bits = [item.get("tag") or "node"]
        if item.get("text"):
            bits.append(f"文字={item['text']}")
        if item.get("placeholder"):
            bits.append(f"placeholder={item['placeholder']}")
        if item.get("name"):
            bits.append(f"name={item['name']}")
        if item.get("id"):
            bits.append(f"id={item['id']}")
        if item.get("href"):
            bits.append(f"href={item['href']}")
        lines.append("- " + " ".join(bits))
    return "\n".join(lines)


def _run(payload: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    db = ctx.get("db")
    if db is None:
        raise SkillError("缺少数据库上下文", 500)
    url = str(payload.get("url") or "").strip()
    goal = str(payload.get("goal") or "").strip()
    if not url or not goal:
        raise SkillError("需要 url 和 goal")
    project_id = payload.get("project_id")
    if not project_id:
        raise SkillError("需要 project_id")
    try:
        env = parse_env(payload.get("env") or {})
    except StepError as exc:
        raise SkillError(str(exc)) from exc

    config = resolve_model(db, payload.get("model_id"))
    try:
        page = snapshot(url, env=env)
    except RunError as exc:
        raise SkillError(str(exc), 503) from exc
    except Exception as exc:  # noqa: BLE001 - browser problems are expected
        raise SkillError(f"打开页面失败：{exc}", 502) from exc

    user_prompt = (
        f"页面地址：{page['url']}\n页面标题：{page['title']}\n\n"
        f"页面文字：\n{page['text'][:2500]}\n\n"
        f"可交互元素：\n{_nodes_text(page['nodes'])}\n\n"
        f"测试目标：{goal}"
    )
    raw = llm_client.chat_json(
        db,
        config,
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        purpose="ui_case_generate",
        prompt_version=PROMPT_VERSION,
        timeout=120.0,
        max_tokens=3000,
    )
    try:
        steps = normalise_steps(raw.get("steps"))
    except StepError as exc:
        raise SkillError(f"模型给的步骤不可用：{exc}", 502) from exc
    if not steps:
        raise SkillError("模型没有给出可执行步骤，请换个说法再试", 502)
    reasoning = str(raw.get("reasoning") or "")[:500]

    case_out = None
    if payload.get("save", True):
        case = models.UiCase(
            project_id=int(project_id),
            title=f"{goal[:60]}",
            module="AI 探索",
            base_url=url,
            env_json=json.dumps(env, ensure_ascii=False),
            steps_json=json.dumps(steps, ensure_ascii=False),
            status="draft",
            source="ai",
            prompt_version=PROMPT_VERSION,
            note=reasoning or None,
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        case_out = {
            "id": case.id,
            "project_id": case.project_id,
            "title": case.title,
            "module": case.module,
            "kind": case.kind,
            "base_url": case.base_url,
            "env": env,
            "steps": steps,
            "status": case.status,
            "source": case.source,
            "prompt_version": case.prompt_version,
            "note": case.note,
            "created_at": case.created_at,
            "updated_at": case.updated_at,
        }

    return {
        "url": page["url"],
        "title": page["title"],
        "nodes": len(page["nodes"]),
        "steps": steps,
        "reasoning": reasoning,
        "case": case_out,
        "model_name": config.model_name,
        "prompt_version": PROMPT_VERSION,
    }


register(
    Skill(
        id="ui.case.generate",
        name="UI 用例生成",
        category="ui",
        description="打开页面抓取快照，由大模型给出可直接执行的 Playwright 步骤，并落库为草稿。",
        input_schema={
            "type": "object",
            "required": ["project_id", "url", "goal"],
            "properties": {
                "project_id": {"type": "integer"},
                "url": {"type": "string"},
                "goal": {"type": "string"},
                "env": {"type": "object"},
                "model_id": {"type": "integer"},
                "save": {"type": "boolean"},
            },
        },
        output_schema={"type": "object"},
        handler=_run,
    )
)
