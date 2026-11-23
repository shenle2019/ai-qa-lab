"""Serve the platform skill handbook as read-only markdown."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

DOCS_DIR = Path(__file__).resolve().parent / "skill_docs"
ZIP_DIR = DOCS_DIR / "zips"
TITLE_RE = re.compile(r"^#\s+(.+)$", re.M)
FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.S)

router = APIRouter(prefix="/api/platform", tags=["skill-docs"])


def _clean(text: str) -> str:
    """Drop the YAML frontmatter so the page starts at the title."""
    return FRONTMATTER_RE.sub("", text, count=1).lstrip("\n")


def _title(text: str, fallback: str) -> str:
    match = TITLE_RE.search(text)
    return match.group(1).strip() if match else fallback


def _slug(path: Path) -> str:
    return path.stem


def _docs() -> list[Path]:
    if not DOCS_DIR.is_dir():
        return []
    return [p for p in sorted(DOCS_DIR.glob("*.md")) if p.stem != "index"]


@router.get("/skill-docs")
def list_skill_docs() -> list[dict]:
    items = []
    for path in _docs():
        text = _clean(path.read_text(encoding="utf-8", errors="replace"))
        items.append(
            {
                "slug": _slug(path),
                "title": _title(text, _slug(path)),
                "chars": len(text),
                "has_zip": (ZIP_DIR / f"{_slug(path)}.zip").is_file(),
            }
        )
    return items


@router.get("/skill-docs/{slug}")
def get_skill_doc(slug: str) -> dict:
    path = DOCS_DIR / f"{slug}.md"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="没有这篇文档")
    text = _clean(path.read_text(encoding="utf-8", errors="replace"))
    return {"slug": slug, "title": _title(text, slug), "markdown": text}


@router.get("/skill-docs/{slug}/download")
def download_skill_doc(slug: str) -> FileResponse:
    """Hand back the packaged skill folder (SKILL.md + references) as a zip."""
    if not re.fullmatch(r"[A-Za-z0-9._-]+", slug):
        raise HTTPException(status_code=400, detail="技能名不合法")
    archive = ZIP_DIR / f"{slug}.zip"
    if not archive.is_file():
        raise HTTPException(status_code=404, detail="这个技能没有可下载的压缩包")
    return FileResponse(archive, media_type="application/zip", filename=f"{slug}.zip")
