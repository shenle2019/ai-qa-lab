"""Requirement management API (Phase 1).

The heavy lifting (LLM prompts, normalisation) lives in the
``requirement.*`` skills; these endpoints only handle storage, uploads and
serialisation.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from . import platform_models
from . import requirement_models as models
from . import requirement_schemas as schemas
from .db import SessionLocal  # noqa: F401 - re-exported for tests
from .deps import get_db
from .requirement_files import extract_text
from .skills import SkillError, run_skill

router = APIRouter(prefix="/api/platform", tags=["requirements"])

UPLOAD_ROOT = Path(__file__).resolve().parents[4] / "data" / "uploads" / "requirements"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def _parse(raw: str) -> dict | None:
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _attachment_out(item: models.RequirementAttachment) -> dict:
    return {
        "id": item.id,
        "filename": item.filename,
        "content_type": item.content_type,
        "size": item.size,
        "chars": len(item.extracted_text or ""),
        "extract_note": item.extract_note or "",
        "created_at": item.created_at,
    }


def _serialize(db: Session, req: models.Requirement, with_messages: bool = True) -> dict:
    attachments = (
        db.query(models.RequirementAttachment)
        .filter(models.RequirementAttachment.requirement_id == req.id)
        .order_by(models.RequirementAttachment.id)
        .all()
    )
    payload = {
        "id": req.id,
        "project_id": req.project_id,
        "title": req.title,
        "body": req.body,
        "status": req.status,
        "priority": req.priority,
        "source_filename": req.source_filename,
        "analysis": _parse(req.analysis_json),
        "plan": _parse(req.plan_json),
        "attachments": [_attachment_out(a) for a in attachments],
        "messages": [],
        "created_at": req.created_at,
        "updated_at": req.updated_at,
    }
    if with_messages:
        rows = (
            db.query(models.RequirementMessage)
            .filter(models.RequirementMessage.requirement_id == req.id)
            .order_by(models.RequirementMessage.id)
            .all()
        )
        payload["messages"] = [
            {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at}
            for m in rows
        ]
    return payload


def _get(db: Session, requirement_id: int) -> models.Requirement:
    req = db.get(models.Requirement, requirement_id)
    if req is None:
        raise HTTPException(status_code=404, detail="需求不存在")
    return req


def _run(skill_id: str, payload: dict, db: Session) -> dict:
    try:
        return run_skill(skill_id, payload, {"db": db})
    except SkillError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/requirements")
def list_requirements(
    project_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Requirement)
    if project_id:
        query = query.filter(models.Requirement.project_id == project_id)
    if status:
        query = query.filter(models.Requirement.status == status)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(models.Requirement.title.like(like))
    rows = query.order_by(models.Requirement.id.desc()).all()
    return [_serialize(db, row, with_messages=False) for row in rows]


@router.post("/requirements", status_code=201)
def create_requirement(body: schemas.RequirementCreate, db: Session = Depends(get_db)):
    if body.status not in schemas.STATUSES:
        raise HTTPException(status_code=400, detail="状态不合法")
    if body.priority not in schemas.PRIORITIES:
        raise HTTPException(status_code=400, detail="优先级不合法")
    project = db.get(platform_models.Project, body.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    req = models.Requirement(
        project_id=body.project_id,
        title=body.title.strip(),
        body=body.body or "",
        status=body.status,
        priority=body.priority,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _serialize(db, req)


@router.get("/requirements/{requirement_id}")
def get_requirement(requirement_id: int, db: Session = Depends(get_db)):
    return _serialize(db, _get(db, requirement_id))


@router.patch("/requirements/{requirement_id}")
def update_requirement(
    requirement_id: int, body: schemas.RequirementUpdate, db: Session = Depends(get_db)
):
    req = _get(db, requirement_id)
    if body.title is not None:
        req.title = body.title.strip()
    if body.body is not None:
        req.body = body.body
    if body.status is not None:
        if body.status not in schemas.STATUSES:
            raise HTTPException(status_code=400, detail="状态不合法")
        req.status = body.status
    if body.priority is not None:
        if body.priority not in schemas.PRIORITIES:
            raise HTTPException(status_code=400, detail="优先级不合法")
        req.priority = body.priority
    db.commit()
    db.refresh(req)
    return _serialize(db, req)


@router.delete("/requirements/{requirement_id}", status_code=204)
def delete_requirement(requirement_id: int, db: Session = Depends(get_db)):
    req = _get(db, requirement_id)
    db.query(models.RequirementAttachment).filter(
        models.RequirementAttachment.requirement_id == req.id
    ).delete()
    db.query(models.RequirementMessage).filter(
        models.RequirementMessage.requirement_id == req.id
    ).delete()
    db.delete(req)
    db.commit()
    return None


@router.post("/requirements/{requirement_id}/attachments", status_code=201)
async def upload_attachment(
    requirement_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    req = _get(db, requirement_id)
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="单文件不能超过 20MB")
    if not data:
        raise HTTPException(status_code=400, detail="文件为空")

    filename = Path(file.filename or "upload").name
    folder = UPLOAD_ROOT / str(req.id)
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix.lower()
    stored = folder / f"{uuid.uuid4().hex}{suffix}"
    stored.write_bytes(data)

    text, note = extract_text(stored, filename)
    item = models.RequirementAttachment(
        requirement_id=req.id,
        filename=filename,
        content_type=file.content_type or "",
        size=len(data),
        stored_path=str(stored),
        extracted_text=text[:200000],
        extract_note=note[:300],
    )
    db.add(item)
    if not req.source_filename:
        req.source_filename = filename
    db.commit()
    db.refresh(item)
    return _attachment_out(item)


@router.delete("/requirements/{requirement_id}/attachments/{attachment_id}", status_code=204)
def delete_attachment(
    requirement_id: int, attachment_id: int, db: Session = Depends(get_db)
):
    item = db.get(models.RequirementAttachment, attachment_id)
    if item is None or item.requirement_id != requirement_id:
        raise HTTPException(status_code=404, detail="附件不存在")
    try:
        Path(item.stored_path).unlink(missing_ok=True)
    except OSError:
        pass
    db.delete(item)
    db.commit()
    return None


@router.get("/requirements/{requirement_id}/attachments/{attachment_id}/download")
def download_attachment(
    requirement_id: int, attachment_id: int, db: Session = Depends(get_db)
):
    item = db.get(models.RequirementAttachment, attachment_id)
    if item is None or item.requirement_id != requirement_id:
        raise HTTPException(status_code=404, detail="附件不存在")
    path = Path(item.stored_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="文件已丢失")
    return FileResponse(path, filename=item.filename)


@router.post("/requirements/{requirement_id}/analyze")
def analyze_requirement(requirement_id: int, db: Session = Depends(get_db)):
    _get(db, requirement_id)
    result = _run("requirement.analyze", {"requirement_id": requirement_id}, db)
    req = _get(db, requirement_id)
    result["requirement"] = _serialize(db, req)
    return result


@router.post("/requirements/{requirement_id}/plan")
def plan_requirement(
    requirement_id: int, body: schemas.PlanIn | None = None, db: Session = Depends(get_db)
):
    _get(db, requirement_id)
    payload = {"requirement_id": requirement_id, "create_plan": True if body is None else body.create_plan}
    result = _run("requirement.plan", payload, db)
    req = _get(db, requirement_id)
    result["requirement"] = _serialize(db, req)
    return result


@router.post("/requirements/{requirement_id}/chat")
def chat_requirement(
    requirement_id: int, body: schemas.ChatIn, db: Session = Depends(get_db)
):
    _get(db, requirement_id)
    result = _run(
        "requirement.chat",
        {"requirement_id": requirement_id, "message": body.message},
        db,
    )
    req = _get(db, requirement_id)
    result["requirement"] = _serialize(db, req)
    return result
