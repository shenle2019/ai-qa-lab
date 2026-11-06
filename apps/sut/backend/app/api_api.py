"""REST layer for API automation: assets, endpoints, cases, runs."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import api_models as models
from . import api_schemas as schemas
from .api_executor import debug_endpoint, diagnose, execute_case, serialise_run
from .api_openapi import SpecError, load_spec, parse_endpoints, spec_meta
from .api_runner import RunError
from .deps import get_db
from .skills import SkillError, run_skill
from .skills.builtin.llm_support import resolve_model

router = APIRouter(prefix="/api/platform", tags=["api-automation"])


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _load(text: str | None, fallback: Any) -> Any:
    try:
        return json.loads(text or "")
    except (json.JSONDecodeError, TypeError):
        return fallback


def _run_skill(skill_id: str, payload: dict, db: Session) -> dict:
    try:
        return run_skill(skill_id, payload, {"db": db})
    except SkillError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


def _asset_out(asset: models.ApiAsset) -> dict:
    return {
        "id": asset.id,
        "project_id": asset.project_id,
        "name": asset.name,
        "source": asset.source,
        "spec_version": asset.spec_version,
        "base_url": asset.base_url,
        "endpoint_count": asset.endpoint_count,
        "created_at": asset.created_at,
    }


def _endpoint_out(endpoint: models.ApiEndpoint, case_count: int = 0) -> dict:
    return {
        "id": endpoint.id,
        "project_id": endpoint.project_id,
        "asset_id": endpoint.asset_id,
        "method": endpoint.method,
        "path": endpoint.path,
        "name": endpoint.name,
        "module": endpoint.module,
        "summary": endpoint.summary,
        "params": _load(endpoint.params_json, []),
        "body": _load(endpoint.body_json, {}),
        "responses": _load(endpoint.responses_json, []),
        "source": endpoint.source,
        "case_count": case_count,
        "created_at": endpoint.created_at,
        "updated_at": endpoint.updated_at,
    }


def _case_out(case: models.ApiCase) -> dict:
    return {
        "id": case.id,
        "project_id": case.project_id,
        "endpoint_id": case.endpoint_id,
        "kind": case.kind,
        "title": case.title,
        "module": case.module,
        "steps": _load(case.steps_json, []),
        "expected": case.expected,
        "status": case.status,
        "source": case.source,
        "prompt_version": case.prompt_version,
        "created_at": case.created_at,
    }


def _case_counts(db: Session, endpoint_ids: list[int]) -> dict[int, int]:
    if not endpoint_ids:
        return {}
    rows = (
        db.query(models.ApiCase.endpoint_id, func.count(models.ApiCase.id))
        .filter(models.ApiCase.endpoint_id.in_(endpoint_ids))
        .group_by(models.ApiCase.endpoint_id)
        .all()
    )
    return {int(row[0]): int(row[1]) for row in rows if row[0] is not None}


# ---------------------------------------------------------------- assets


@router.get("/api-assets")
def list_assets(project_id: int | None = None, db: Session = Depends(get_db)) -> list[dict]:
    query = db.query(models.ApiAsset)
    if project_id:
        query = query.filter(models.ApiAsset.project_id == project_id)
    return [_asset_out(item) for item in query.order_by(models.ApiAsset.id.desc()).all()]


@router.post("/api-assets/import", status_code=201)
def import_spec(payload: schemas.ImportSpecIn, db: Session = Depends(get_db)) -> dict:
    try:
        spec = load_spec(payload.spec)
        meta = spec_meta(spec)
        rows = parse_endpoints(spec)
    except SpecError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    asset = models.ApiAsset(
        project_id=payload.project_id,
        name=(payload.name or meta["title"])[:200],
        source="openapi",
        spec_version=meta["version"],
        base_url=meta["base_url"],
        endpoint_count=len(rows),
    )
    db.add(asset)
    db.flush()

    for row in rows:
        db.add(
            models.ApiEndpoint(
                project_id=payload.project_id,
                asset_id=asset.id,
                method=row["method"],
                path=row["path"],
                name=row["name"],
                module=row["module"],
                summary=row["summary"],
                params_json=_dump(row["params"]),
                body_json=_dump(row["body"]),
                responses_json=_dump(row["responses"]),
                source="openapi",
            )
        )
    db.commit()
    return {**_asset_out(asset), "imported": len(rows)}


@router.delete("/api-assets/{asset_id}", status_code=204)
def delete_asset(asset_id: int, db: Session = Depends(get_db)) -> Response:
    asset = db.get(models.ApiAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="接口资产不存在")
    db.query(models.ApiEndpoint).filter(models.ApiEndpoint.asset_id == asset_id).delete()
    db.delete(asset)
    db.commit()
    return Response(status_code=204)


# ------------------------------------------------------------- endpoints


@router.get("/api-endpoints/modules")
def list_modules(project_id: int | None = None, db: Session = Depends(get_db)) -> list[dict]:
    query = db.query(models.ApiEndpoint.module, func.count(models.ApiEndpoint.id))
    if project_id:
        query = query.filter(models.ApiEndpoint.project_id == project_id)
    rows = query.group_by(models.ApiEndpoint.module).order_by(models.ApiEndpoint.module).all()
    return [{"module": str(item[0] or "未分组"), "count": int(item[1])} for item in rows]


@router.get("/api-endpoints")
def list_endpoints(
    project_id: int | None = None,
    module: str | None = None,
    q: str | None = None,
    method: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(models.ApiEndpoint)
    if project_id:
        query = query.filter(models.ApiEndpoint.project_id == project_id)
    if module:
        query = query.filter(models.ApiEndpoint.module == module)
    if method:
        query = query.filter(models.ApiEndpoint.method == method.upper())
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            models.ApiEndpoint.path.like(like) | models.ApiEndpoint.name.like(like)
        )
    items = query.order_by(models.ApiEndpoint.id.asc()).limit(limit).all()
    counts = _case_counts(db, [item.id for item in items])
    return [_endpoint_out(item, counts.get(item.id, 0)) for item in items]


@router.post("/api-endpoints", status_code=201)
def create_endpoint(payload: schemas.EndpointCreate, db: Session = Depends(get_db)) -> dict:
    method = payload.method.upper()
    if method not in schemas.METHODS:
        raise HTTPException(status_code=400, detail="不支持的请求方法")
    endpoint = models.ApiEndpoint(
        project_id=payload.project_id,
        asset_id=payload.asset_id,
        method=method,
        path=payload.path,
        name=payload.name or f"{method} {payload.path}",
        module=payload.module or "未分组",
        summary=payload.summary,
        params_json=_dump(payload.params),
        body_json=_dump(payload.body),
        responses_json=_dump(payload.responses),
        source="manual",
    )
    db.add(endpoint)
    db.commit()
    return _endpoint_out(endpoint)


@router.get("/api-endpoints/{endpoint_id}")
def get_endpoint(endpoint_id: int, db: Session = Depends(get_db)) -> dict:
    endpoint = db.get(models.ApiEndpoint, endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="接口不存在")
    counts = _case_counts(db, [endpoint_id])
    return _endpoint_out(endpoint, counts.get(endpoint_id, 0))


@router.patch("/api-endpoints/{endpoint_id}")
def update_endpoint(
    endpoint_id: int, payload: schemas.EndpointUpdate, db: Session = Depends(get_db)
) -> dict:
    endpoint = db.get(models.ApiEndpoint, endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="接口不存在")
    data = payload.model_dump(exclude_unset=True)
    if "method" in data and data["method"]:
        method = str(data["method"]).upper()
        if method not in schemas.METHODS:
            raise HTTPException(status_code=400, detail="不支持的请求方法")
        endpoint.method = method
    for field in ("path", "name", "module", "summary"):
        if field in data and data[field] is not None:
            setattr(endpoint, field, data[field])
    if "params" in data and data["params"] is not None:
        endpoint.params_json = _dump(data["params"])
    if "body" in data and data["body"] is not None:
        endpoint.body_json = _dump(data["body"])
    if "responses" in data and data["responses"] is not None:
        endpoint.responses_json = _dump(data["responses"])
    db.commit()
    return _endpoint_out(endpoint)


@router.delete("/api-endpoints/{endpoint_id}", status_code=204)
def delete_endpoint(endpoint_id: int, db: Session = Depends(get_db)) -> Response:
    endpoint = db.get(models.ApiEndpoint, endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="接口不存在")
    db.query(models.ApiCase).filter(models.ApiCase.endpoint_id == endpoint_id).delete()
    db.delete(endpoint)
    db.commit()
    return Response(status_code=204)


@router.post("/api-endpoints/{endpoint_id}/debug")
def debug(
    endpoint_id: int, payload: schemas.DebugIn, db: Session = Depends(get_db)
) -> dict:
    endpoint = db.get(models.ApiEndpoint, endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="接口不存在")
    try:
        result = debug_endpoint(
            db,
            endpoint,
            method=endpoint.method,
            base_url=payload.base_url,
            headers=payload.headers,
            params=payload.params,
            body=payload.body,
            expect_status=payload.expect_status,
        )
    except RunError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


# ----------------------------------------------------------------- cases


@router.get("/api-cases")
def list_cases(
    project_id: int | None = None,
    kind: str | None = None,
    endpoint_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(models.ApiCase)
    if project_id:
        query = query.filter(models.ApiCase.project_id == project_id)
    if kind:
        query = query.filter(models.ApiCase.kind == kind)
    if endpoint_id:
        query = query.filter(models.ApiCase.endpoint_id == endpoint_id)
    if status:
        query = query.filter(models.ApiCase.status == status)
    return [_case_out(item) for item in query.order_by(models.ApiCase.id.desc()).all()]


@router.post("/api-cases/generate")
def generate_cases(payload: schemas.GenerateCasesIn, db: Session = Depends(get_db)) -> dict:
    return _run_skill(
        "api.case.generate",
        {
            "endpoint_id": payload.endpoint_id,
            "count": payload.count,
            "kb_id": payload.kb_id,
            "model_id": payload.model_id,
        },
        db,
    )


@router.post("/api-cases/generate-scenario")
def generate_scenario(
    payload: schemas.GenerateScenarioIn, db: Session = Depends(get_db)
) -> dict:
    return _run_skill(
        "api.scenario.generate",
        {
            "project_id": payload.project_id,
            "endpoint_ids": payload.endpoint_ids,
            "goal": payload.goal,
            "model_id": payload.model_id,
        },
        db,
    )


@router.post("/api-cases", status_code=201)
def create_case(payload: schemas.CaseCreate, db: Session = Depends(get_db)) -> dict:
    if not payload.steps:
        raise HTTPException(status_code=400, detail="用例至少需要一个步骤")
    case = models.ApiCase(
        project_id=payload.project_id,
        endpoint_id=payload.endpoint_id,
        kind=payload.kind,
        title=payload.title,
        module=payload.module,
        steps_json=_dump(payload.steps),
        expected=payload.expected,
        status=payload.status,
        source="manual",
    )
    db.add(case)
    db.commit()
    return _case_out(case)


@router.patch("/api-cases/{case_id}")
def update_case(case_id: int, payload: schemas.CaseUpdate, db: Session = Depends(get_db)) -> dict:
    case = db.get(models.ApiCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="用例不存在")
    data = payload.model_dump(exclude_unset=True)
    for field in ("title", "module", "expected", "status"):
        if field in data and data[field] is not None:
            setattr(case, field, data[field])
    if "steps" in data and data["steps"] is not None:
        if not data["steps"]:
            raise HTTPException(status_code=400, detail="用例至少需要一个步骤")
        case.steps_json = _dump(data["steps"])
    db.commit()
    return _case_out(case)


@router.delete("/api-cases/{case_id}", status_code=204)
def delete_case(case_id: int, db: Session = Depends(get_db)) -> Response:
    case = db.get(models.ApiCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="用例不存在")
    db.delete(case)
    db.commit()
    return Response(status_code=204)


@router.post("/api-cases/{case_id}/run")
def run_case(
    case_id: int,
    base_url: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    case = db.get(models.ApiCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="用例不存在")
    try:
        return execute_case(db, case, base_url=base_url)
    except RunError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ------------------------------------------------------------------ runs


@router.get("/api-runs")
def list_runs(
    project_id: int | None = None,
    status: str | None = None,
    case_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(models.ApiRun)
    if project_id:
        query = query.filter(models.ApiRun.project_id == project_id)
    if status:
        query = query.filter(models.ApiRun.status == status)
    if case_id:
        query = query.filter(models.ApiRun.case_id == case_id)
    items = query.order_by(models.ApiRun.id.desc()).limit(limit).all()
    return [serialise_run(item) for item in items]


@router.get("/api-runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)) -> dict:
    run = db.get(models.ApiRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return serialise_run(run)


@router.post("/api-runs/{run_id}/diagnose")
def diagnose_run(
    run_id: int, model_id: int | None = None, db: Session = Depends(get_db)
) -> dict:
    run = db.get(models.ApiRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    if run.status == "passed":
        raise HTTPException(status_code=400, detail="这条记录是成功的，不需要归因")
    config = resolve_model(db, model_id)
    text = diagnose(db, run, config)
    return {"run_id": run.id, "ai_root_cause": text}
