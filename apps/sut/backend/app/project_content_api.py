"""CRUD for project modules and members."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import project_content_models as models
from .deps import get_db

router = APIRouter(prefix="/api/platform", tags=["project-content"])

ROLES = {"测试", "开发", "产品", "运维", "负责人"}


class ModuleIn(BaseModel):
    project_id: int
    name: str = Field(min_length=1, max_length=80)
    owner: str = Field(default="", max_length=60)
    description: str = ""


class ModulePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    owner: str | None = Field(default=None, max_length=60)
    description: str | None = None


class ModuleOut(BaseModel):
    id: int
    project_id: int
    name: str
    owner: str
    description: str
    created_at: object


class MemberIn(BaseModel):
    project_id: int
    name: str = Field(min_length=1, max_length=60)
    role: str = "测试"
    email: str = Field(default="", max_length=120)


class MemberPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    role: str | None = None
    email: str | None = Field(default=None, max_length=120)


def _module_out(row: models.ProjectModule) -> dict:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "name": row.name,
        "owner": row.owner,
        "description": row.description,
        "created_at": row.created_at,
    }


def _member_out(row: models.ProjectMember) -> dict:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "name": row.name,
        "role": row.role,
        "email": row.email,
        "created_at": row.created_at,
    }


@router.get("/modules")
def list_modules(project_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(models.ProjectModule)
        .filter(models.ProjectModule.project_id == project_id)
        .order_by(models.ProjectModule.id)
        .all()
    )
    return [_module_out(row) for row in rows]


@router.post("/modules", status_code=201)
def create_module(payload: ModuleIn, db: Session = Depends(get_db)):
    exists = (
        db.query(models.ProjectModule)
        .filter(
            models.ProjectModule.project_id == payload.project_id,
            models.ProjectModule.name == payload.name,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="同名模块已存在")
    row = models.ProjectModule(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _module_out(row)


@router.patch("/modules/{module_id}")
def update_module(module_id: int, payload: ModulePatch, db: Session = Depends(get_db)):
    row = db.get(models.ProjectModule, module_id)
    if row is None:
        raise HTTPException(status_code=404, detail="模块不存在")
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有需要修改的字段")
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return _module_out(row)


@router.delete("/modules/{module_id}", status_code=204)
def delete_module(module_id: int, db: Session = Depends(get_db)):
    row = db.get(models.ProjectModule, module_id)
    if row is None:
        raise HTTPException(status_code=404, detail="模块不存在")
    db.delete(row)
    db.commit()
    return Response(status_code=204)


@router.get("/members")
def list_members(project_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(models.ProjectMember)
        .filter(models.ProjectMember.project_id == project_id)
        .order_by(models.ProjectMember.id)
        .all()
    )
    return [_member_out(row) for row in rows]


@router.post("/members", status_code=201)
def create_member(payload: MemberIn, db: Session = Depends(get_db)):
    if payload.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"角色只能是 {'/'.join(sorted(ROLES))}")
    exists = (
        db.query(models.ProjectMember)
        .filter(
            models.ProjectMember.project_id == payload.project_id,
            models.ProjectMember.name == payload.name,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="同名成员已存在")
    row = models.ProjectMember(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _member_out(row)


@router.patch("/members/{member_id}")
def update_member(member_id: int, payload: MemberPatch, db: Session = Depends(get_db)):
    row = db.get(models.ProjectMember, member_id)
    if row is None:
        raise HTTPException(status_code=404, detail="成员不存在")
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有需要修改的字段")
    if "role" in data and data["role"] not in ROLES:
        raise HTTPException(status_code=400, detail=f"角色只能是 {'/'.join(sorted(ROLES))}")
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return _member_out(row)


@router.delete("/members/{member_id}", status_code=204)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    row = db.get(models.ProjectMember, member_id)
    if row is None:
        raise HTTPException(status_code=404, detail="成员不存在")
    db.delete(row)
    db.commit()
    return Response(status_code=204)
