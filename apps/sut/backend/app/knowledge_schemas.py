from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=400)
    project_id: int | None = None
    chunk_size: int = Field(default=600, ge=100, le=4000)
    chunk_overlap: int = Field(default=100, ge=0, le=1000)


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=400)
    chunk_size: int | None = Field(default=None, ge=100, le=4000)
    chunk_overlap: int | None = Field(default=None, ge=0, le=1000)


class KnowledgeDocumentOut(BaseModel):
    id: int
    kb_id: int
    filename: str
    content_type: str
    size: int
    char_count: int
    chunk_count: int
    source: str
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeBaseOut(BaseModel):
    id: int
    project_id: int | None
    name: str
    description: str
    chunk_size: int
    chunk_overlap: int
    document_count: int = 0
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime


class TextDocumentIn(BaseModel):
    filename: str = Field(default="pasted.txt", max_length=255)
    text: str = Field(min_length=1)


class ChunkOut(BaseModel):
    id: int
    document_id: int
    seq: int
    char_count: int
    text: str

    model_config = {"from_attributes": True}


class SearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchHit(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    seq: int
    score: float
    snippet: str


class SearchOut(BaseModel):
    kb_id: int
    query: str
    took_ms: int
    hits: list[SearchHit]
