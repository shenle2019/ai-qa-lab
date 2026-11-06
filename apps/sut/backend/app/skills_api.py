"""HTTP surface for the skill registry.

``GET  /api/platform/skills``            -> list skills (optional ?category=)
``GET  /api/platform/skills/{id}``       -> one skill descriptor
``POST /api/platform/skills/{id}/run``   -> run it with a JSON payload
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from .deps import get_db
from .skills import SkillError, get, list_skills, run_skill

router = APIRouter(prefix="/api/platform", tags=["skills"])


@router.get("/skills")
def list_all_skills(category: str | None = None) -> list[dict]:
    return [s.to_dict() for s in list_skills(category)]


@router.get("/skills/{skill_id}")
def get_skill(skill_id: str) -> dict:
    skill = get(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"skill {skill_id!r} not found")
    return skill.to_dict()


@router.post("/skills/{skill_id}/run")
def run(skill_id: str, payload: dict = Body(default={}), db: Session = Depends(get_db)) -> dict:
    try:
        result = run_skill(skill_id, payload, {"db": db})
    except SkillError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return {"ok": True, "skill_id": skill_id, "result": result}
