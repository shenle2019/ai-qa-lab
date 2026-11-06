"""HTTP routes for UI automation: cases, execution, exploration, chat."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from . import ui_models as models
from . import ui_schemas as schemas
from .deps import get_db
from .skills import SkillError, run_skill
from .ui_steps import StepError, normalise_steps, parse_env, render_script

router = APIRouter(prefix="/api/platform", tags=["ui-automation"])

SHOT_DIR = Path(__file__).resolve().parents[4] / "data" / "ui-shots"


def _run_skill(skill_id: str, payload: dict, db: Session) -> dict:
    try:
        return run_skill(skill_id, payload, {"db": db})
    except SkillError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


def _env_of(raw: str | None) -> dict[str, str]:
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}


def _steps_of(raw: str | None) -> list:
    try:
        value = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _case_out(case: models.UiCase) -> dict:
    return {
        "id": case.id,
        "project_id": case.project_id,
        "title": case.title,
        "module": case.module,
        "kind": case.kind,
        "base_url": case.base_url,
        "env": _env_of(case.env_json),
        "steps": _steps_of(case.steps_json),
        "status": case.status,
        "source": case.source,
        "prompt_version": case.prompt_version,
        "note": case.note,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
    }


def _run_out(run: models.UiRun) -> dict:
    return {
        "id": run.id,
        "project_id": run.project_id,
        "case_id": run.case_id,
        "title": run.title,
        "status": run.status,
        "duration_ms": run.duration_ms,
        "steps": _steps_of(run.steps_json),
        "screenshot": run.screenshot,
        "error": run.error,
        "created_at": run.created_at,
    }


def _get_case(db: Session, case_id: int) -> models.UiCase:
    case = db.get(models.UiCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="用例不存在")
    return case


@router.get("/ui-cases")
def list_ui_cases(
    project_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.UiCase)
    if project_id:
        query = query.filter(models.UiCase.project_id == project_id)
    if status:
        query = query.filter(models.UiCase.status == status)
    rows = query.order_by(models.UiCase.id.desc()).all()
    return [_case_out(row) for row in rows]


@router.post("/ui-cases", status_code=201)
def create_ui_case(payload: schemas.UiCaseCreate, db: Session = Depends(get_db)):
    if payload.status not in schemas.STATUSES:
        raise HTTPException(status_code=400, detail="状态不合法")
    try:
        steps = normalise_steps(payload.steps)
    except StepError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    case = models.UiCase(
        project_id=payload.project_id,
        title=payload.title.strip(),
        module=payload.module or "未分组",
        base_url=payload.base_url,
        env_json=json.dumps(payload.env, ensure_ascii=False),
        steps_json=json.dumps(steps, ensure_ascii=False),
        status=payload.status,
        source="manual",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return _case_out(case)


@router.get("/ui-cases/{case_id}")
def get_ui_case(case_id: int, db: Session = Depends(get_db)):
    return _case_out(_get_case(db, case_id))


@router.patch("/ui-cases/{case_id}")
def update_ui_case(case_id: int, payload: schemas.UiCaseUpdate, db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有需要修改的字段")
    if "status" in data and data["status"] not in schemas.STATUSES:
        raise HTTPException(status_code=400, detail="状态不合法")
    if "steps" in data:
        try:
            data["steps_json"] = json.dumps(normalise_steps(data.pop("steps")), ensure_ascii=False)
        except StepError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if "env" in data:
        try:
            data["env_json"] = json.dumps(parse_env(data.pop("env")), ensure_ascii=False)
        except StepError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    for key, value in data.items():
        setattr(case, key, value)
    db.commit()
    db.refresh(case)
    return _case_out(case)


@router.delete("/ui-cases/{case_id}", status_code=204)
def delete_ui_case(case_id: int, db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    db.query(models.UiRun).filter(models.UiRun.case_id == case.id).delete()
    db.delete(case)
    db.commit()
    return Response(status_code=204)


@router.get("/ui-cases/{case_id}/script")
def ui_case_script(case_id: int, db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    script = render_script(
        case.title,
        case.base_url,
        _env_of(case.env_json),
        _steps_of(case.steps_json),
    )
    return {"case_id": case.id, "title": case.title, "script": script}


@router.post("/ui-cases/{case_id}/run")
def run_ui_case(case_id: int, db: Session = Depends(get_db)):
    _get_case(db, case_id)
    return _run_skill("ui.run", {"case_id": case_id}, db)


@router.get("/ui-runs")
def list_ui_runs(
    project_id: int | None = None,
    limit: int = Query(default=30, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(models.UiRun)
    if project_id:
        query = query.filter(models.UiRun.project_id == project_id)
    rows = query.order_by(models.UiRun.id.desc()).limit(limit).all()
    return [_run_out(row) for row in rows]


@router.get("/ui-runs/{run_id}")
def get_ui_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(models.UiRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    data = _run_out(run)
    if run.screenshot:
        path = SHOT_DIR / run.screenshot
        if path.exists():
            data["screenshot_data"] = base64.b64encode(path.read_bytes()).decode("ascii")
    return data


@router.get("/ui-runs/{run_id}/screenshot")
def ui_run_screenshot(run_id: int, db: Session = Depends(get_db)):
    run = db.get(models.UiRun, run_id)
    if run is None or not run.screenshot:
        raise HTTPException(status_code=404, detail="没有截图")
    path = SHOT_DIR / run.screenshot
    if not path.exists():
        raise HTTPException(status_code=404, detail="截图文件不存在")
    return FileResponse(path, media_type="image/png")


@router.post("/ui-explore")
def explore(payload: schemas.ExploreIn, db: Session = Depends(get_db)):
    return _run_skill(
        "ui.case.generate",
        {
            "project_id": payload.project_id,
            "url": payload.url,
            "goal": payload.goal,
            "env": payload.env,
            "model_id": payload.model_id,
            "save": payload.save,
        },
        db,
    )


@router.post("/ui-chat")
def ui_chat(payload: schemas.ChatIn, db: Session = Depends(get_db)):
    return _run_skill(
        "ui.chat",
        {
            "url": payload.url,
            "question": payload.question,
            "env": payload.env,
            "model_id": payload.model_id,
        },
        db,
    )
