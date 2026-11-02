from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TicketStatus = Literal["open", "in_progress", "closed"]
TicketPriority = Literal["low", "medium", "high"]


class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    priority: TicketPriority = "medium"


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    priority: TicketPriority | None = None


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime

    model_config = {"from_attributes": True}


class KBQuery(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)
