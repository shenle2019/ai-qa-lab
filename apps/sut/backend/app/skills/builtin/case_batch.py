"""Builtin skill: batch operations on test cases (review flow + delete)."""

from __future__ import annotations

from ..registry import Skill, SkillError, register
from ... import platform_models as models

# action -> (required current status or None, target status)
FLOW = {
    "submit_review": ("draft", "pending_review"),
    "approve": ("pending_review", "approved"),
    "reject": ("pending_review", "rejected"),
    "draft": (None, "draft"),
}
ACTIONS = set(FLOW) | {"delete"}


def _run(payload, ctx):
    db = ctx.get("db")
    if db is None:
        raise SkillError("db session missing")
    action = str(payload.get("action") or "").strip()
    if action not in ACTIONS:
        raise SkillError(f"action 只能是 {sorted(ACTIONS)}")
    ids = payload.get("ids") or []
    if not isinstance(ids, list) or not ids:
        raise SkillError("ids 不能为空")
    reviewer = str(payload.get("reviewer") or "local")
    comment = str(payload.get("comment") or "")

    updated = 0
    skipped = []
    for raw_id in ids:
        case = db.get(models.TestCase, int(raw_id))
        if case is None:
            skipped.append({"id": raw_id, "reason": "用例不存在"})
            continue

        if action == "delete":
            db.delete(case)
            updated += 1
            continue

        need, target = FLOW[action]
        if need is not None and case.status != need:
            skipped.append({"id": case.id, "reason": f"当前状态 {case.status}，需要 {need}"})
            continue

        case.status = target
        if action in {"approve", "reject"}:
            db.add(
                models.CaseReview(
                    case_id=case.id,
                    reviewer=reviewer,
                    decision=target,
                    comment=comment,
                )
            )
        updated += 1

    db.commit()
    return {"action": action, "updated": updated, "skipped": skipped}


SKILL = register(
    Skill(
        id="case.batch",
        name="批量用例操作",
        category="case",
        description="批量提交审核 / 通过 / 驳回 / 退回草稿 / 删除，逐条返回被跳过的原因。",
        input_schema={
            "type": "object",
            "required": ["action", "ids"],
            "properties": {
                "action": {"type": "string", "enum": sorted(ACTIONS)},
                "ids": {"type": "array", "items": {"type": "integer"}},
                "reviewer": {"type": "string"},
                "comment": {"type": "string"},
            },
        },
        output_schema={"type": "object"},
        handler=_run,
    )
)
