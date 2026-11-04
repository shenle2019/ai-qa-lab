import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import llm_models, models, platform_models, schemas
from .db import Base, SessionLocal, engine
from .model_api import router as model_router
from .platform_api import router as platform_router
from .schema_migrations import ensure_columns
from .workbench import router as workbench_router

Base.metadata.create_all(bind=engine)
ensure_columns(engine)

if os.getenv("SEED_DEMO") == "1":
    from .seed import seed_demo_data

    seed_demo_data()

app = FastAPI(title="AI Knowledge Ops SUT", version="0.1.0")
app.include_router(workbench_router)
app.include_router(platform_router)
app.include_router(model_router)

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
LEARNING_DIR = Path(__file__).resolve().parents[4] / "docs" / "learning"
PORTFOLIO_DIR = Path(__file__).resolve().parents[4] / "docs" / "portfolio"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "sut", "version": app.version}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui/")


@app.get("/api/tickets", response_model=list[schemas.TicketOut])
def list_tickets(db: Session = Depends(get_db)):
    return db.query(models.Ticket).order_by(models.Ticket.id.desc()).all()


@app.post("/api/tickets", response_model=schemas.TicketOut, status_code=201)
def create_ticket(payload: schemas.TicketCreate, db: Session = Depends(get_db)):
    ticket = models.Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/api/tickets/{ticket_id}", response_model=schemas.TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
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
    ticket = db.get(models.Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    db.delete(ticket)
    db.commit()
    return Response(status_code=204)


@app.post("/api/kb/query")
def query_knowledge_base(payload: schemas.KBQuery) -> dict:
    # Week 0 mock: replaced by a real RAG pipeline in module 08.
    return {
        "answer": f"[mock] 关于“{payload.question}”的知识库回答",
        "sources": [],
        "top_k": payload.top_k,
    }


if FRONTEND_DIST.exists():
    app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="ui")

if LEARNING_DIR.exists():
    app.mount("/learning", StaticFiles(directory=str(LEARNING_DIR), html=True), name="learning")

if PORTFOLIO_DIR.exists():
    app.mount("/portfolio", StaticFiles(directory=str(PORTFOLIO_DIR), html=True), name="portfolio")
