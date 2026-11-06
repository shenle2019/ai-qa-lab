"""Platform accounts shown on the 用户管理 page.

The platform itself authenticates with a single service key (see auth.py); this
table is the team directory: who can enter the platform and with what role.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from .db import Base
from .deps import get_db
from .timeutils import utcnow

ROLES = {"管理员", "测试", "开发", "产品", "访客"}
STATUSES = {"active", "disabled"}


class PlatformUser(Base):
    __tablename__ = "platform_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(160), default="")
    role: Mapped[str] = mapped_column(String(20), default="测试", index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    email: str = Field(default="", max_length=160)
    role: str = Field(default="测试")
    status: str = Field(default="active")
    note: str = Field(default="", max_length=400)


class UserUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=160)
    role: str | None = None
    status: str | None = None
    note: str | None = Field(default=None, max_length=400)


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    status: str
    note: str
    created_at: datetime


router = APIRouter(prefix="/api/platform", tags=["users"])


def _out(user: PlatformUser) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email or "",
        role=user.role,
        status=user.status,
        note=user.note or "",
        created_at=user.created_at,
    )


def _validate(role: str | None, status: str | None) -> None:
    if role is not None and role not in ROLES:
        raise HTTPException(status_code=400, detail=f"角色必须是 {sorted(ROLES)} 之一")
    if status is not None and status not in STATUSES:
        raise HTTPException(status_code=400, detail=f"状态必须是 {sorted(STATUSES)} 之一")


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)) -> list[UserOut]:
    rows = db.execute(select(PlatformUser).order_by(PlatformUser.id)).scalars().all()
    return [_out(row) for row in rows]


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    _validate(payload.role, payload.status)
    exists = db.execute(select(PlatformUser).where(PlatformUser.name == name)).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=409, detail="同名用户已存在")
    user = PlatformUser(
        name=name,
        email=payload.email.strip(),
        role=payload.role,
        status=payload.status,
        note=payload.note.strip(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _out(user)


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> UserOut:
    user = db.get(PlatformUser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    _validate(payload.role, payload.status)
    if payload.email is not None:
        user.email = payload.email.strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.status is not None:
        user.status = payload.status
    if payload.note is not None:
        user.note = payload.note.strip()
    db.commit()
    db.refresh(user)
    return _out(user)


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)) -> Response:
    user = db.get(PlatformUser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return Response(status_code=204)
