from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from . import case_executor, case_generator, llm_client, llm_models, rate_limit, report_generator, settings
from . import platform_models as models
from . import platform_schemas as schemas
from .deps import get_db
from .skills import SkillError, run_skill
from .timeutils import utcnow

router = APIRouter(prefix="/api/platform", tags=["platform"])


def _run_skill(skill_id: str, payload: dict, db: Session) -> dict:
    """Run a registered skill and turn its errors into HTTP errors."""
    try:
        return run_skill(skill_id, payload, {"db": db})
    except SkillError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc



def _execution_out(
    db: Session,
    execution: models.TestExecution,
    results: list[models.TestResult] | None = None,
) -> schemas.ExecutionOut:
    if results is None:
        results = (
            db.query(models.TestResult)
            .filter(models.TestResult.execution_id == execution.id)
            .order_by(models.TestResult.id)
            .all()
        )
    return schemas.ExecutionOut(
        id=execution.id,
        plan_id=execution.plan_id,
        status=execution.status,
        total=execution.total,
        passed=execution.passed,
        failed=execution.failed,
        skipped=execution.skipped,
        duration_ms=execution.duration_ms,
        started_at=execution.started_at,
        results=[schemas.ResultOut.model_validate(result) for result in results],
    )


def _create_execution(db: Session, plan: models.TestPlan, results: list[schemas.ResultIn]) -> schemas.ExecutionOut:
    passed = sum(1 for item in results if item.status in {"passed", "xfailed", "xpassed"})
    failed = sum(1 for item in results if item.status in {"failed", "error"})
    skipped = sum(1 for item in results if item.status == "skipped")
    status = "failed" if failed else "passed"
    execution = models.TestExecution(
        plan_id=plan.id,
        status=status,
        total=len(results),
        passed=passed,
        failed=failed,
        skipped=skipped,
        duration_ms=sum(item.duration_ms for item in results),
        started_at=utcnow(),
    )
    db.add(execution)
    db.flush()
    for item in results:
        db.add(
            models.TestResult(
                execution_id=execution.id,
                case_id=item.case_id,
                case_name=item.case_name,
                status=item.status,
                duration_ms=item.duration_ms,
                message=item.message,
            )
        )
    plan.status = status
    db.commit()
    db.refresh(execution)
    return _execution_out(db, execution)


@router.get("/summary", response_model=schemas.SummaryOut)
def summary(db: Session = Depends(get_db)):
    projects = db.query(models.Project).count()
    cases = db.query(models.TestCase).count()
    plans = db.query(models.TestPlan).count()
    executions = db.query(models.TestExecution).count()
    defects = db.query(models.Defect).count()
    open_defects = db.query(models.Defect).filter(models.Defect.status == "open").count()
    recent = (
        db.query(models.TestExecution)
        .order_by(models.TestExecution.id.desc())
        .limit(10)
        .all()
    )
    passed = sum(item.passed for item in recent)
    failed = sum(item.failed for item in recent)
    pass_rate = passed / (passed + failed) if passed + failed else 0.0
    return schemas.SummaryOut(
        projects=projects,
        cases=cases,
        plans=plans,
        executions=executions,
        defects=defects,
        open_defects=open_defects,
        pass_rate=round(pass_rate, 4),
        results_passed=passed,
        results_failed=failed,
        results_total=passed + failed,
    )


@router.get("/projects", response_model=list[schemas.ProjectOut])
def list_projects(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Project)
        .order_by(models.Project.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.post("/projects", response_model=schemas.ProjectOut, status_code=201)
def create_project(
    payload: schemas.ProjectCreate,
    response: Response,
    db: Session = Depends(get_db),
):
    existing = db.query(models.Project).filter(models.Project.name == payload.name).first()
    if existing:
        response.status_code = 200
        return existing
    project = models.Project(name=payload.name, description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return project


@router.get("/cases", response_model=list[schemas.CaseOut])
def list_cases(
    project_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(models.TestCase)
    if project_id is not None:
        query = query.filter(models.TestCase.project_id == project_id)
    return query.order_by(models.TestCase.id.desc()).offset(offset).limit(limit).all()


@router.post("/cases", response_model=schemas.CaseOut, status_code=201)
def create_case(payload: schemas.CaseCreate, db: Session = Depends(get_db)):
    if db.get(models.Project, payload.project_id) is None:
        raise HTTPException(status_code=404, detail="project not found")
    case = models.TestCase(**payload.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.post("/cases/batch")
def batch_cases(payload: dict, db: Session = Depends(get_db)):
    """Batch review/delete flow. Declared before /cases/{case_id} to keep the path literal."""
    return _run_skill("case.batch", payload, db)


@router.post("/generate-cases", response_model=schemas.GeneratedCasesOut, status_code=201)
def generate_cases(
    payload: schemas.GenerateCasesRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    rate_limit.enforce_llm_quota(request)
    project = db.get(models.Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")

    if payload.model_id is not None:
        config = db.get(llm_models.ModelConfig, payload.model_id)
        if config is None:
            raise HTTPException(status_code=404, detail="model not found")
    else:
        config = (
            db.query(llm_models.ModelConfig)
            .filter(llm_models.ModelConfig.enabled.is_(True))
            .order_by(llm_models.ModelConfig.id)
            .first()
        )
    if config is None or not config.enabled:
        raise HTTPException(status_code=400, detail="没有启用的模型，请先在模型中心配置")

    try:
        items = case_generator.generate(db, config, payload.requirement, payload.max_cases)
    except llm_client.LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    created: list[models.TestCase] = []
    for item in items:
        case = models.TestCase(
            project_id=project.id,
            title=item["title"],
            module=item["module"],
            priority=item["priority"],
            steps=case_generator.steps_to_text(item["steps"]),
            expected=item["expected"],
            status="draft",
            source="ai",
            prompt_version=case_generator.PROMPT_VERSION,
            steps_json=case_generator.steps_to_json(item["steps"]),
        )
        db.add(case)
        created.append(case)
    db.commit()
    for case in created:
        db.refresh(case)
    return schemas.GeneratedCasesOut(
        model_name=config.model_name,
        prompt_version=case_generator.PROMPT_VERSION,
        cases=[schemas.CaseOut.model_validate(case) for case in created],
    )


@router.post("/cases/{case_id}/submit-review", response_model=schemas.CaseOut)
def submit_case_review(case_id: int, db: Session = Depends(get_db)):
    case = db.get(models.TestCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    if case.status != "draft":
        raise HTTPException(status_code=409, detail="只有草稿用例可以提交审核")
    case.status = "pending_review"
    db.commit()
    db.refresh(case)
    return case


@router.post("/cases/{case_id}/review", response_model=schemas.CaseReviewOut, status_code=201)
def review_case(case_id: int, payload: schemas.CaseReviewCreate, db: Session = Depends(get_db)):
    case = db.get(models.TestCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    if case.status != "pending_review":
        raise HTTPException(status_code=409, detail="只有待审核用例可以审核")
    case.status = payload.decision
    review = models.CaseReview(
        case_id=case.id,
        reviewer=payload.reviewer,
        decision=payload.decision,
        comment=payload.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/cases/{case_id}/reviews", response_model=list[schemas.CaseReviewOut])
def list_case_reviews(case_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.CaseReview)
        .filter(models.CaseReview.case_id == case_id)
        .order_by(models.CaseReview.id.desc())
        .all()
    )


@router.get("/cases/{case_id}", response_model=schemas.CaseOut)
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.get(models.TestCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    return case


@router.patch("/cases/{case_id}", response_model=schemas.CaseOut)
def update_case(case_id: int, payload: dict, db: Session = Depends(get_db)):
    body = dict(payload)
    body["case_id"] = case_id
    result = _run_skill("case.update", body, db)
    return db.get(models.TestCase, int(result["case"]["id"]))


@router.delete("/cases/{case_id}", status_code=204)
def delete_case(case_id: int, db: Session = Depends(get_db)):
    case = db.get(models.TestCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    db.delete(case)
    db.commit()
    return Response(status_code=204)


@router.get("/plans", response_model=list[schemas.PlanOut])
def list_plans(
    project_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(models.TestPlan)
    if project_id is not None:
        query = query.filter(models.TestPlan.project_id == project_id)
    return query.order_by(models.TestPlan.id.desc()).offset(offset).limit(limit).all()


@router.post("/plans", response_model=schemas.PlanOut, status_code=201)
def create_plan(payload: schemas.PlanCreate, db: Session = Depends(get_db)):
    if db.get(models.Project, payload.project_id) is None:
        raise HTTPException(status_code=404, detail="project not found")
    plan = models.TestPlan(project_id=payload.project_id, name=payload.name)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/plans/{plan_id}", response_model=schemas.PlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.get(models.TestPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="plan not found")
    return plan


@router.post("/plans/{plan_id}/run", response_model=schemas.ExecutionOut, status_code=201)
def run_plan(plan_id: int, payload: schemas.ExecutionCreate, db: Session = Depends(get_db)):
    if settings.is_production():
        raise HTTPException(
            status_code=410,
            detail="client-reported results are disabled in production; use /execute",
        )
    plan = db.get(models.TestPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="plan not found")
    case_ids = [item.case_id for item in payload.results if item.case_id]
    if case_ids:
        blocked = (
            db.query(models.TestCase)
            .filter(models.TestCase.id.in_(case_ids), models.TestCase.status != "approved")
            .count()
        )
        if blocked:
            raise HTTPException(status_code=409, detail="只有已审核通过的用例可以执行")
    return _create_execution(db, plan, payload.results)


@router.post("/plans/{plan_id}/execute", response_model=schemas.ExecutionOut, status_code=202)
def execute_plan(
    plan_id: int,
    background_tasks: BackgroundTasks,
    payload: schemas.ExecutePlanRequest | None = None,
    db: Session = Depends(get_db),
):
    plan = db.get(models.TestPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="plan not found")

    query = db.query(models.TestCase).filter(
        models.TestCase.project_id == plan.project_id,
        models.TestCase.status == "approved",
    )
    if payload and payload.case_ids:
        query = query.filter(models.TestCase.id.in_(payload.case_ids))
    cases = query.order_by(models.TestCase.id).all()
    if not cases:
        raise HTTPException(status_code=400, detail="没有已审核通过的用例可执行")

    base_url = payload.base_url if payload else None
    if base_url and not base_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="base_url 必须以 http:// 或 https:// 开头")

    execution = models.TestExecution(
        plan_id=plan.id,
        status="running",
        started_at=utcnow(),
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    background_tasks.add_task(
        case_executor.run_execution,
        execution.id,
        plan.id,
        [case.id for case in cases],
        base_url,
    )
    return _execution_out(db, execution, [])


@router.get("/executions", response_model=list[schemas.ExecutionOut])
def list_executions(
    plan_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(models.TestExecution)
    if plan_id is not None:
        query = query.filter(models.TestExecution.plan_id == plan_id)
    executions = query.order_by(models.TestExecution.id.desc()).offset(offset).limit(limit).all()
    if not executions:
        return []
    execution_ids = [execution.id for execution in executions]
    grouped: dict[int, list[models.TestResult]] = {execution_id: [] for execution_id in execution_ids}
    results = (
        db.query(models.TestResult)
        .filter(models.TestResult.execution_id.in_(execution_ids))
        .order_by(models.TestResult.id)
        .all()
    )
    for result in results:
        grouped.setdefault(result.execution_id, []).append(result)
    return [_execution_out(db, execution, grouped.get(execution.id, [])) for execution in executions]


@router.get("/executions/{execution_id}", response_model=schemas.ExecutionOut)
def get_execution(execution_id: int, db: Session = Depends(get_db)):
    execution = db.get(models.TestExecution, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="execution not found")
    return _execution_out(db, execution)


@router.get("/executions/{execution_id}/report", response_class=HTMLResponse)
def execution_report(execution_id: int, db: Session = Depends(get_db)):
    execution = db.get(models.TestExecution, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="execution not found")
    results = (
        db.query(models.TestResult)
        .filter(models.TestResult.execution_id == execution.id)
        .order_by(models.TestResult.id)
        .all()
    )
    return HTMLResponse(report_generator.render(execution, results))


@router.get("/defects", response_model=list[schemas.DefectOut])
def list_defects(
    project_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(models.Defect)
    if project_id is not None:
        query = query.filter(models.Defect.project_id == project_id)
    return query.order_by(models.Defect.id.desc()).offset(offset).limit(limit).all()


@router.post("/defects", response_model=schemas.DefectOut, status_code=201)
def create_defect(payload: schemas.DefectCreate, db: Session = Depends(get_db)):
    if db.get(models.Project, payload.project_id) is None:
        raise HTTPException(status_code=404, detail="project not found")
    defect = models.Defect(**payload.model_dump())
    db.add(defect)
    db.commit()
    db.refresh(defect)
    return defect


@router.patch("/defects/{defect_id}", response_model=schemas.DefectOut)
def update_defect(defect_id: int, payload: schemas.DefectUpdate, db: Session = Depends(get_db)):
    defect = db.get(models.Defect, defect_id)
    if defect is None:
        raise HTTPException(status_code=404, detail="defect not found")
    defect.status = payload.status
    db.commit()
    db.refresh(defect)
    return defect


@router.post("/import/minipytest", response_model=schemas.ExecutionOut, status_code=201)
def import_minipytest(payload: schemas.ImportRequest, db: Session = Depends(get_db)):
    report = payload.report
    if payload.plan_id:
        plan = db.get(models.TestPlan, payload.plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="plan not found")
    else:
        project = db.query(models.Project).filter(models.Project.name == "导入报告").first()
        if project is None:
            project = models.Project(name="导入报告", description="从测试报告自动导入")
            db.add(project)
            db.flush()
        plan = models.TestPlan(
            project_id=project.id,
            name=f"minipytest {report.get('started_at', '')} {uuid4().hex[:6]}",
        )
        db.add(plan)
        db.flush()

    status_map = {
        "passed": "passed",
        "failed": "failed",
        "error": "error",
        "skipped": "skipped",
        "xfailed": "xfailed",
        "xpassed": "xpassed",
    }
    results: list[schemas.ResultIn] = []
    for item in report.get("tests", []):
        failure = item.get("failure") or {}
        message = str(failure.get("message", ""))
        if len(message) > 2000:
            message = message[:1997] + "…"
        results.append(
            schemas.ResultIn(
                case_id=None,
                case_name=item.get("name", "") or item.get("id", ""),
                status=status_map.get(item.get("status", "error"), "error"),
                duration_ms=int(item.get("duration_ms", 0)),
                message=message,
            )
        )
    return _create_execution(db, plan, results)


@router.post("/seed", response_model=schemas.SummaryOut)
def seed_demo(db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.name == "AI 质量平台演示").first()
    if project is None:
        project = models.Project(name="AI 质量平台演示", description="模块 07 演示数据")
        db.add(project)
        db.flush()

        cases = [
            (
                "工单列表返回 200",
                "api",
                "high",
                '[{"action":"GET","target":"/api/tickets","data":"","assert":"status=200"}]',
                "GET /api/tickets 返回 200",
            ),
            (
                "创建工单并回查",
                "api",
                "high",
                '[{"action":"POST","target":"/api/tickets","data":"{\\"title\\":\\"seed case\\",\\"priority\\":\\"medium\\"}","assert":"status=201"}]',
                "POST /api/tickets 返回 201",
            ),
            ("Web 工单页可打开", "web", "medium", "[]", "Web 自动化暂未接入平台执行"),
            ("Android Settings 可启动", "app", "medium", "[]", "App 自动化暂未接入平台执行"),
        ]
        for title, module, priority, steps_json, steps in cases:
            db.add(
                models.TestCase(
                    project_id=project.id,
                    title=title,
                    module=module,
                    priority=priority,
                    steps=steps,
                    expected="状态符合预期",
                    steps_json=steps_json,
                )
            )
        db.flush()

        plan = models.TestPlan(project_id=project.id, name="演示回归计划", status="draft")
        db.add(plan)
        db.flush()

        results = [
            schemas.ResultIn(case_name="工单列表返回 200", status="passed", duration_ms=120),
            schemas.ResultIn(case_name="创建工单并回查", status="passed", duration_ms=180),
            schemas.ResultIn(case_name="Web 工单页可打开", status="failed", duration_ms=2400, message="页面超时"),
            schemas.ResultIn(case_name="Android Settings 可启动", status="skipped", duration_ms=0, message="模拟器未启动"),
        ]
        _create_execution(db, plan, results)

        db.add(
            models.Defect(
                project_id=project.id,
                title="Web 工单页在冷启动时超时",
                severity="high",
                status="open",
            )
        )
        db.commit()

    return summary(db)
