"""Best-effort text extraction for requirement attachments (Phase 1).

No extra dependency is required:

* plain text / markdown / json / csv / yaml / log  -> decoded directly
* docx -> unzipped ``word/document.xml`` and stripped of tags
* pdf  -> decompressed content streams, text operators only (best effort)

Anything else, or a failed parse, returns a human-readable note instead of
raising: an upload must never fail because the browser was able to store a file
we cannot read yet.
"""

from __future__ import annotations

import re
import zipfile
import zlib
from pathlib import Path

TEXT_SUFFIXES = {
    ".md",
    ".markdown",
    ".txt",
    ".text",
    ".json",
    ".csv",
    ".yaml",
    ".yml",
    ".log",
    ".html",
    ".htm",
}


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _docx_text(path: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
    except (KeyError, zipfile.BadZipFile) as exc:
        return "", f"DOCX 解析失败：{exc}"
    xml = xml.replace("</w:p>", "\n").replace("<w:br/>", "\n")
    text = re.sub(r"<[^>]+>", "", xml)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text, ""


def _pdf_text(path: Path) -> tuple[str, str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return "", f"PDF 读取失败：{exc}"

    pieces: list[str] = []
    for stream in re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.S):
        data = stream.group(1)
        try:
            data = zlib.decompress(data)
        except zlib.error:
            pass
        if b"Tj" not in data and b"TJ" not in data:
            continue
        for token in re.finditer(rb"\((?:\\.|[^\\)])*\)", data):
            chunk = token.group(0)[1:-1]
            chunk = chunk.replace(b"\\(", b"(").replace(b"\\)", b")").replace(b"\\\\", b"\\")
            pieces.append(chunk.decode("latin-1", errors="replace"))

    text = " ".join(pieces).strip()
    if not text:
        return "", "PDF 未能提取到文本（可能是扫描件或加密），请直接粘贴正文"
    return re.sub(r"\s{2,}", " ", text), ""


def extract_text(path: Path, filename: str = "") -> tuple[str, str]:
    """Return ``(text, note)``. ``note`` is non-empty when extraction was partial."""
    suffix = Path(filename or path.name).suffix.lower()
    try:
        if suffix in TEXT_SUFFIXES:
            return _read_text(path).strip(), ""
        if suffix == ".docx":
            return _docx_text(path)
        if suffix == ".pdf":
            return _pdf_text(path)
    except OSError as exc:
        return "", f"文件读取失败：{exc}"
    return "", f"暂不支持 {suffix or '该类型'} 文本提取，将仅保留附件"
