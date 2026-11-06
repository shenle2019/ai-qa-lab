"""REST endpoints for test environments."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .deps import get_db
from .environment_models import Environment

router = APIRouter(prefix="/api/platform", tags=["environments"])

KINDS = ("dev", "test", "staging", "prod")


class EnvironmentIn(BaseModel):
    project_id: int
    name: str = Field(min_length=1, max_length=80)
    kind: str = "test"
    base_url: str = Field(default="", max_length=500)
    variables: dict[str, str] = Field(default_factory=dict)
    note: str = ""


class EnvironmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    kind: str | None = None
    base_url: str | None = Field(default=None, max_length=500)
    variables: dict[str, str] | None = None
    note: str | None = None


def _variables(raw: str) -> dict[str, str]:
    try:
        value = json.loads(raw or "{}")
    except ValueError:
        return {}
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}


def _out(item: Environment) -> dict:
    return {
        "id": item.id,
        "project_id": item.project_id,
        "name": item.name,
        "kind": item.kind,
        "base_url": item.base_url,
        "variables": _variables(item.variables_json),
        "note": item.note,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _check_kind(kind: str) -> str:
    if kind not in KINDS:
        raise HTTPException(status_code=400, detail=f"环境类型只能是 {', '.join(KINDS)}")
    return kind


def _get(db: Session, env_id: int) -> Environment:
    item = db.get(Environment, env_id)
    if item is None:
        raise HTTPException(status_code=404, detail="环境不存在")
    return item


@router.get("/environments")
def list_environments(project_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Environment)
    if project_id is not None:
        query = query.filter(Environment.project_id == project_id)
    items = query.order_by(Environment.id.desc()).all()
    return [_out(item) for item in items]


@router.post("/environments", status_code=201)
def create_environment(payload: EnvironmentIn, db: Session = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="环境名称不能为空")
    _check_kind(payload.kind)
    exists = (
        db.query(Environment)
        .filter(Environment.project_id == payload.project_id, Environment.name == name)
        .first()
    )
    if exists is not None:
        raise HTTPException(status_code=409, detail="这个项目下已经有同名环境")
    item = Environment(
        project_id=payload.project_id,
        name=name,
        kind=payload.kind,
        base_url=payload.base_url.strip(),
        variables_json=json.dumps(payload.variables, ensure_ascii=False),
        note=payload.note,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _out(item)


@router.patch("/environments/{env_id}")
def update_environment(env_id: int, payload: EnvironmentUpdate, db: Session = Depends(get_db)):
    item = _get(db, env_id)
    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="环境名称不能为空")
        clash = (
            db.query(Environment)
            .filter(
                Environment.project_id == item.project_id,
                Environment.name == name,
                Environment.id != item.id,
            )
            .first()
        )
        if clash is not None:
            raise HTTPException(status_code=409, detail="这个项目下已经有同名环境")
        item.name = name
    if payload.kind is not None:
        item.kind = _check_kind(payload.kind)
    if payload.base_url is not None:
        item.base_url = payload.base_url.strip()
    if payload.variables is not None:
        item.variables_json = json.dumps(payload.variables, ensure_ascii=False)
    if payload.note is not None:
        item.note = payload.note
    db.commit()
    db.refresh(item)
    return _out(item)


@router.delete("/environments/{env_id}", status_code=204)
def delete_environment(env_id: int, db: Session = Depends(get_db)):
    item = _get(db, env_id)
    db.delete(item)
    db.commit()
    return Response(status_code=204)
