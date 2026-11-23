"""Serve the platform skill handbook as read-only markdown."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

DOCS_DIR = Path(__file__).resolve().parent / "skill_docs"
TITLE_RE = re.compile(r"^#\s+(.+)$", re.M)

router = APIRouter(prefix="/api/platform", tags=["skill-docs"])


def _title(text: str, fallback: str) -> str:
    match = TITLE_RE.search(text)
    return match.group(1).strip() if match else fallback


def _slug(path: Path) -> str:
    return path.stem


def _docs() -> list[Path]:
    if not DOCS_DIR.is_dir():
        return []
    return sorted(DOCS_DIR.glob("*.md"))


@router.get("/skill-docs")
def list_skill_docs() -> list[dict]:
    items = []
    for path in _docs():
        text = path.read_text(encoding="utf-8", errors="replace")
        items.append(
            {
                "slug": _slug(path),
                "title": _title(text, _slug(path)),
                "chars": len(text),
            }
        )
    return items


@router.get("/skill-docs/{slug}")
def get_skill_doc(slug: str) -> dict:
    path = DOCS_DIR / f"{slug}.md"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="没有这篇文档")
    text = path.read_text(encoding="utf-8", errors="replace")
    return {"slug": slug, "title": _title(text, slug), "markdown": text}
