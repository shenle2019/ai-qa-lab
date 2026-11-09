import logging
import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import (
    api_models,
    environment_models,
    kb,
    knowledge_models,
    llm_models,
    models,
    platform_models,
    project_content_models,
    requirement_models,
    schemas,
    settings,
    ui_models,
    users_api,
)
from .api_api import router as api_router
from .auth import auth_guard
from .db import Base, engine
from .deps import get_db
from .environment_api import router as environment_router
from .knowledge_api import router as knowledge_router
from .middleware import request_context
from .model_api import router as model_router
from .platform_api import router as platform_router
from .project_content_api import router as project_content_router
from .requirement_api import router as requirement_router
from .schema_migrations import ensure_columns
from .skills_api import router as skills_router
from .ui_api import router as ui_router
from .users_api import router as users_router
from .workbench import router as workbench_router

logging.basicConfig(level=logging.INFO, format="%(message)s")

Base.metadata.create_all(bind=engine)
ensure_columns(engine)

if settings.seed_enabled():
    from .seed import seed_demo_data

    seed_demo_data()

app = FastAPI(
    title="AI Knowledge Ops SUT",
    version="1.2.1",
    docs_url="/docs" if settings.docs_enabled() else None,
    redoc_url="/redoc" if settings.docs_enabled() else None,
    openapi_url="/openapi.json" if settings.docs_enabled() else None,
)

origins = settings.cors_origins()
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    )

app.middleware("http")(auth_guard)
app.middleware("http")(request_context)

app.include_router(workbench_router)
app.include_router(platform_router)
app.include_router(model_router)
app.include_router(skills_router)
app.include_router(requirement_router)
app.include_router(knowledge_router)
app.include_router(api_router)
app.include_router(ui_router)
app.include_router(project_content_router)
app.include_router(users_router)
app.include_router(environment_router)

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
LEARNING_DIR = Path(__file__).resolve().parents[4] / "docs" / "learning"
PORTFOLIO_DIR = Path(__file__).resolve().parents[4] / "docs" / "portfolio"



def _ui_automation_ready() -> bool:
    """UI automation needs the playwright package plus a downloaded browser."""
    try:
        import playwright  # noqa: F401
    except Exception:  # noqa: BLE001 - optional dependency
        return False
    from .ui_runner import BROWSERS

    return (BROWSERS / "chromium-1248").exists() or (BROWSERS / "chromium_headless_shell-1248").exists()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "sut",
        "version": app.version,
        "auth": "production" if settings.is_production() else "dev",
        "docs": settings.docs_enabled(),
        "ui_automation": _ui_automation_ready(),
    }


@app.get("/ready")
def ready() -> dict:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"database not ready: {exc}") from exc
    return {"status": "ready"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui/")


@app.post("/api/auth/verify")
def verify_api_key() -> dict:
    """Return 200 only when the supplied key passes the auth guard.

    The UI calls this right after saving a key so a typo is reported as a
    wrong key instead of surfacing later as a failed write.
    """
    return {"ok": True}


@app.get("/api/tickets", response_model=list[schemas.TicketOut])
def list_tickets(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    return (
        db.query(models.Ticket)
        .order_by(models.Ticket.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.post("/api/tickets", response_model=schemas.TicketOut, status_code=201)
def create_ticket(payload: schemas.TicketCreate, db: Session = Depends(get_db)):
    ticket = models.Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


SQLITE_MAX_INT = 2**63 - 1


def _ensure_sqlite_int(value: int) -> None:
    if value > SQLITE_MAX_INT or value < -SQLITE_MAX_INT - 1:
        raise HTTPException(status_code=422, detail="ticket id out of range")


@app.get("/api/tickets/{ticket_id}", response_model=schemas.TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    _ensure_sqlite_int(ticket_id)
    ticket = db.get(models.Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    return ticket


@app.patch("/api/tickets/{ticket_id}", response_model=schemas.TicketOut)
def update_ticket(
    ticket_id: int,
    payload: schemas.TicketUpdate,
    db: Session = Depends(get_db),
):
    _ensure_sqlite_int(ticket_id)
    ticket = db.get(models.Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, key, value)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.delete("/api/tickets/{ticket_id}", status_code=204)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    _ensure_sqlite_int(ticket_id)
    ticket = db.get(models.Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    db.delete(ticket)
    db.commit()
    return Response(status_code=204)


@app.post("/api/kb/query")
def query_knowledge_base(payload: schemas.KBQuery, db: Session = Depends(get_db)) -> dict:
    matches = kb.search(db, payload.question, payload.top_k)
    return {
        "answer": kb.answer(payload.question, matches),
        "sources": matches,
        "top_k": payload.top_k,
    }


if FRONTEND_DIST.exists():
    app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="ui")

if LEARNING_DIR.exists():
    app.mount("/learning", StaticFiles(directory=str(LEARNING_DIR), html=True), name="learning")

if PORTFOLIO_DIR.exists():
    app.mount("/portfolio", StaticFiles(directory=str(PORTFOLIO_DIR), html=True), name="portfolio")
