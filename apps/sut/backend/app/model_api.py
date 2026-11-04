from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from . import llm_client, llm_models, llm_schemas
from .db import SessionLocal

router = APIRouter(prefix="/api/platform", tags=["models"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _to_out(config: llm_models.ModelConfig) -> llm_schemas.ModelConfigOut:
    return llm_schemas.ModelConfigOut(
        id=config.id,
        name=config.name,
        provider=config.provider,
        base_url=config.base_url,
        model_name=config.model_name,
        enabled=config.enabled,
        has_api_key=bool(llm_client.resolve_api_key(config)),
        api_key_masked=llm_client.mask_key(config.api_key),
        created_at=config.created_at,
    )


@router.get("/models", response_model=list[llm_schemas.ModelConfigOut])
def list_models(db: Session = Depends(get_db)):
    return [_to_out(item) for item in db.query(llm_models.ModelConfig).order_by(llm_models.ModelConfig.id).all()]


@router.post("/models", response_model=llm_schemas.ModelConfigOut, status_code=201)
def create_model(payload: llm_schemas.ModelConfigCreate, db: Session = Depends(get_db)):
    existing = db.query(llm_models.ModelConfig).filter(llm_models.ModelConfig.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="model name already exists")
    config = llm_models.ModelConfig(**payload.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return _to_out(config)


@router.patch("/models/{model_id}", response_model=llm_schemas.ModelConfigOut)
def update_model(model_id: int, payload: llm_schemas.ModelConfigUpdate, db: Session = Depends(get_db)):
    config = db.get(llm_models.ModelConfig, model_id)
    if config is None:
        raise HTTPException(status_code=404, detail="model not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return _to_out(config)


@router.post("/models/{model_id}/test", response_model=llm_schemas.ModelTestResult)
def test_model(model_id: int, db: Session = Depends(get_db)):
    config = db.get(llm_models.ModelConfig, model_id)
    if config is None:
        raise HTTPException(status_code=404, detail="model not found")
    started = time.perf_counter()
    try:
        llm_client.chat_json(
            db,
            config,
            [{"role": "user", "content": '只回复 JSON: {"ok": true}'}],
            purpose="connectivity_test",
            prompt_version="test",
            timeout=20.0,
            max_tokens=20,
        )
        return llm_schemas.ModelTestResult(
            ok=True,
            latency_ms=int((time.perf_counter() - started) * 1000),
            message="连接成功",
        )
    except llm_client.LLMError as exc:
        return llm_schemas.ModelTestResult(
            ok=False,
            latency_ms=int((time.perf_counter() - started) * 1000),
            message=str(exc),
        )


@router.get("/model-calls", response_model=list[llm_schemas.LLMCallOut])
def list_model_calls(limit: int = Query(default=20, ge=1, le=200), db: Session = Depends(get_db)):
    return (
        db.query(llm_models.LLMCall)
        .order_by(llm_models.LLMCall.id.desc())
        .limit(limit)
        .all()
    )
