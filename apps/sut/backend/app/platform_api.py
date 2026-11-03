from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from . import platform_models as models
from . import platform_schemas as schemas
from .db import SessionLocal

router = APIRouter(prefix="/api/platform", tags=["platform"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _execution_out(db: Session, execution: models.TestExecution) -> schemas.ExecutionOut:
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
        started_at=datetime.utcnow(),
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
    latest = db.query(models.TestExecution).order_by(models.TestExecution.id.desc()).first()
    pass_rate = 0.0
    if latest and latest.passed + latest.failed:
        pass_rate = latest.passed / (latest.passed + latest.failed)
    return schemas.SummaryOut(
        projects=projects,
        cases=cases,
        plans=plans,
        executions=executions,
        defects=defects,
        open_defects=open_defects,
        pass_rate=round(pass_rate, 4),
    )


@router.get("/projects", response_model=list[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).order_by(models.Project.id.desc()).all()


@router.post("/projects", response_model=schemas.ProjectOut, status_code=201)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Project).filter(models.Project.name == payload.name).first()
    if existing:
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
def list_cases(project_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    query = db.query(models.TestCase)
    if project_id is not None:
        query = query.filter(models.TestCase.project_id == project_id)
    return query.order_by(models.TestCase.id.desc()).all()


@router.post("/cases", response_model=schemas.CaseOut, status_code=201)
def create_case(payload: schemas.CaseCreate, db: Session = Depends(get_db)):
    if db.get(models.Project, payload.project_id) is None:
        raise HTTPException(status_code=404, detail="project not found")
    case = models.TestCase(**payload.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("/plans", response_model=list[schemas.PlanOut])
def list_plans(project_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    query = db.query(models.TestPlan)
    if project_id is not None:
        query = query.filter(models.TestPlan.project_id == project_id)
    return query.order_by(models.TestPlan.id.desc()).all()


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
    plan = db.get(models.TestPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="plan not found")
    return _create_execution(db, plan, payload.results)


@router.get("/executions", response_model=list[schemas.ExecutionOut])
def list_executions(plan_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    query = db.query(models.TestExecution)
    if plan_id is not None:
        query = query.filter(models.TestExecution.plan_id == plan_id)
    executions = query.order_by(models.TestExecution.id.desc()).all()
    return [_execution_out(db, execution) for execution in executions]


@router.get("/executions/{execution_id}", response_model=schemas.ExecutionOut)
def get_execution(execution_id: int, db: Session = Depends(get_db)):
    execution = db.get(models.TestExecution, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="execution not found")
    return _execution_out(db, execution)


@router.get("/defects", response_model=list[schemas.DefectOut])
def list_defects(project_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    query = db.query(models.Defect)
    if project_id is not None:
        query = query.filter(models.Defect.project_id == project_id)
    return query.order_by(models.Defect.id.desc()).all()


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
            name=f"minipytest {report.get('started_at', '')}",
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
        results.append(
            schemas.ResultIn(
                case_id=None,
                case_name=item.get("name", "") or item.get("id", ""),
                status=status_map.get(item.get("status", "error"), "error"),
                duration_ms=int(item.get("duration_ms", 0)),
                message=str(failure.get("message", ""))[:2000],
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
            ("工单列表返回 200", "api", "high"),
            ("创建工单并回查", "api", "high"),
            ("Web 工单页可打开", "web", "medium"),
            ("Android Settings 可启动", "app", "medium"),
        ]
        for title, module, priority in cases:
            db.add(
                models.TestCase(
                    project_id=project.id,
                    title=title,
                    module=module,
                    priority=priority,
                    steps="执行对应自动化用例",
                    expected="状态符合预期",
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
