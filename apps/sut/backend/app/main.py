from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .db import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Knowledge Ops SUT", version="0.1.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "sut", "version": app.version}


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


@app.post("/api/kb/query")
def query_knowledge_base(payload: schemas.KBQuery) -> dict:
    # Week 0 mock: replaced by a real RAG pipeline in module 08.
    return {
        "answer": f"[mock] 关于“{payload.question}”的知识库回答",
        "sources": [],
        "top_k": payload.top_k,
    }
