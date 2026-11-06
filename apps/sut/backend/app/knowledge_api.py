"""Knowledge base API: libraries, documents, chunks and retrieval trials."""

from __future__ import annotations

import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from . import knowledge_models as models
from . import knowledge_schemas as schemas
from .deps import get_db
from .knowledge_chunker import chunk_text
from .knowledge_search import search as run_search
from .requirement_files import extract_text

router = APIRouter(prefix="/api/platform", tags=["knowledge"])

UPLOAD_ROOT = Path(__file__).resolve().parents[4] / "data" / "uploads" / "knowledge"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def _get_kb(db: Session, kb_id: int) -> models.KnowledgeBase:
    item = db.get(models.KnowledgeBase, kb_id)
    if not item:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return item


def _counts(db: Session, kb_id: int) -> tuple[int, int]:
    documents = db.query(models.KnowledgeDocument).filter(models.KnowledgeDocument.kb_id == kb_id).count()
    chunks = db.query(models.KnowledgeChunk).filter(models.KnowledgeChunk.kb_id == kb_id).count()
    return documents, chunks


def _kb_out(db: Session, item: models.KnowledgeBase) -> dict:
    documents, chunks = _counts(db, item.id)
    return {
        "id": item.id,
        "project_id": item.project_id,
        "name": item.name,
        "description": item.description,
        "chunk_size": item.chunk_size,
        "chunk_overlap": item.chunk_overlap,
        "document_count": documents,
        "chunk_count": chunks,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def ingest_text(
    db: Session,
    kb: models.KnowledgeBase,
    *,
    text: str,
    filename: str,
    content_type: str = "text/plain",
    size: int = 0,
    source: str = "text",
    note: str = "",
) -> models.KnowledgeDocument:
    clean = (text or "").strip()
    if not clean:
        raise HTTPException(status_code=400, detail="文档没有可用文本，无法分块")
    pieces = chunk_text(clean, kb.chunk_size, kb.chunk_overlap)
    if not pieces:
        raise HTTPException(status_code=400, detail="分块结果为空，请检查文档内容")
    document = models.KnowledgeDocument(
        kb_id=kb.id,
        filename=filename or "untitled.txt",
        content_type=content_type,
        size=size or len(clean.encode("utf-8")),
        char_count=len(clean),
        chunk_count=len(pieces),
        source=source,
        note=note,
    )
    db.add(document)
    db.flush()
    for index, piece in enumerate(pieces):
        db.add(
            models.KnowledgeChunk(
                kb_id=kb.id,
                document_id=document.id,
                seq=index,
                text=piece,
                char_count=len(piece),
            )
        )
    db.commit()
    db.refresh(document)
    return document


@router.get("/knowledge-bases", response_model=list[schemas.KnowledgeBaseOut])
def list_bases(
    project_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(models.KnowledgeBase)
    if project_id is not None:
        query = query.filter(models.KnowledgeBase.project_id == project_id)
    items = query.order_by(models.KnowledgeBase.id.desc()).all()
    return [_kb_out(db, item) for item in items]


@router.post("/knowledge-bases", response_model=schemas.KnowledgeBaseOut, status_code=201)
def create_base(payload: schemas.KnowledgeBaseCreate, db: Session = Depends(get_db)) -> dict:
    existing = (
        db.query(models.KnowledgeBase)
        .filter(models.KnowledgeBase.name == payload.name)
        .filter(models.KnowledgeBase.project_id == payload.project_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="同名知识库已存在")
    item = models.KnowledgeBase(
        project_id=payload.project_id,
        name=payload.name.strip(),
        description=payload.description,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _kb_out(db, item)


@router.get("/knowledge-bases/{kb_id}", response_model=schemas.KnowledgeBaseOut)
def get_base(kb_id: int, db: Session = Depends(get_db)) -> dict:
    return _kb_out(db, _get_kb(db, kb_id))


@router.patch("/knowledge-bases/{kb_id}", response_model=schemas.KnowledgeBaseOut)
def update_base(kb_id: int, payload: schemas.KnowledgeBaseUpdate, db: Session = Depends(get_db)) -> dict:
    item = _get_kb(db, kb_id)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and not str(data["name"]).strip():
        raise HTTPException(status_code=400, detail="名称不能为空")
    for field, value in data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return _kb_out(db, item)


@router.delete("/knowledge-bases/{kb_id}", status_code=204)
def delete_base(kb_id: int, db: Session = Depends(get_db)):
    item = _get_kb(db, kb_id)
    db.query(models.KnowledgeChunk).filter(models.KnowledgeChunk.kb_id == kb_id).delete()
    db.query(models.KnowledgeDocument).filter(models.KnowledgeDocument.kb_id == kb_id).delete()
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.get("/knowledge-bases/{kb_id}/documents", response_model=list[schemas.KnowledgeDocumentOut])
def list_documents(kb_id: int, db: Session = Depends(get_db)) -> list[models.KnowledgeDocument]:
    _get_kb(db, kb_id)
    return (
        db.query(models.KnowledgeDocument)
        .filter(models.KnowledgeDocument.kb_id == kb_id)
        .order_by(models.KnowledgeDocument.id.desc())
        .all()
    )


@router.post(
    "/knowledge-bases/{kb_id}/documents/text",
    response_model=schemas.KnowledgeDocumentOut,
    status_code=201,
)
def add_text_document(
    kb_id: int, payload: schemas.TextDocumentIn, db: Session = Depends(get_db)
) -> models.KnowledgeDocument:
    kb = _get_kb(db, kb_id)
    return ingest_text(
        db,
        kb,
        text=payload.text,
        filename=payload.filename,
        content_type="text/plain",
        source="text",
    )


@router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=schemas.KnowledgeDocumentOut,
    status_code=201,
)
async def upload_document(
    kb_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
) -> models.KnowledgeDocument:
    kb = _get_kb(db, kb_id)
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="单个文件不能超过 20MB")
    if not raw:
        raise HTTPException(status_code=400, detail="文件为空")

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "upload.bin").name
    target = UPLOAD_ROOT / f"kb{kb_id}-{int(time.time() * 1000)}-{safe_name}"
    target.write_bytes(raw)

    text, note = extract_text(target, safe_name)
    if not (text or "").strip():
        target.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=note or "无法从该文件提取文本，请改用纯文本或直接粘贴正文",
        )
    return ingest_text(
        db,
        kb,
        text=text,
        filename=safe_name,
        content_type=file.content_type or "application/octet-stream",
        size=len(raw),
        source="upload",
        note=note,
    )


@router.delete("/knowledge-documents/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.get(models.KnowledgeDocument, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    db.query(models.KnowledgeChunk).filter(models.KnowledgeChunk.document_id == document_id).delete()
    db.delete(document)
    db.commit()
    return Response(status_code=204)


@router.get("/knowledge-documents/{document_id}/chunks", response_model=list[schemas.ChunkOut])
def list_chunks(
    document_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[models.KnowledgeChunk]:
    if not db.get(models.KnowledgeDocument, document_id):
        raise HTTPException(status_code=404, detail="文档不存在")
    return (
        db.query(models.KnowledgeChunk)
        .filter(models.KnowledgeChunk.document_id == document_id)
        .order_by(models.KnowledgeChunk.seq.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.post("/knowledge-bases/{kb_id}/search", response_model=schemas.SearchOut)
def search_base(kb_id: int, payload: schemas.SearchIn, db: Session = Depends(get_db)) -> dict:
    _get_kb(db, kb_id)
    started = time.perf_counter()
    hits = run_search(db, kb_id, payload.query, payload.top_k)
    took = int((time.perf_counter() - started) * 1000)
    return {"kb_id": kb_id, "query": payload.query, "took_ms": took, "hits": hits}
