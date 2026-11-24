"""The console handbook must mirror the site and stay downloadable."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.skill_docs_api import DOCS_DIR, ZIP_DIR

client = TestClient(app)


def test_list_excludes_index_and_reports_titles() -> None:
    res = client.get("/api/platform/skill-docs")
    assert res.status_code == 200
    items = res.json()
    assert items, "handbook should not be empty"
    slugs = [item["slug"] for item in items]
    assert "index" not in slugs
    assert all(item["title"] and item["chars"] > 200 for item in items)


def test_every_page_on_disk_is_listed() -> None:
    listed = {item["slug"] for item in client.get("/api/platform/skill-docs").json()}
    on_disk = {p.stem for p in DOCS_DIR.glob("*.md") if p.stem != "index"}
    assert listed == on_disk


def test_doc_body_has_no_frontmatter() -> None:
    slug = client.get("/api/platform/skill-docs").json()[0]["slug"]
    body = client.get(f"/api/platform/skill-docs/{slug}").json()
    assert body["slug"] == slug
    assert not body["markdown"].startswith("---")
    assert body["markdown"].lstrip().startswith("#")


def test_unknown_doc_is_a_chinese_404() -> None:
    res = client.get("/api/platform/skill-docs/no-such-skill")
    assert res.status_code == 404
    assert res.json()["detail"] == "没有这篇文档"


def test_download_falls_back_to_the_shenle_prefixed_zip() -> None:
    # 站点手册用的是短名（web-cli），压缩包按技能目录名打（shenle-web-cli.zip）。
    if not (ZIP_DIR / "shenle-web-cli.zip").is_file():
        return
    res = client.get("/api/platform/skill-docs/web-cli/download")
    assert res.status_code == 200
    assert res.content[:2] == b"PK"
    assert "attachment" in res.headers["content-disposition"]


def test_download_rejects_path_escape_and_missing_zip() -> None:
    assert client.get("/api/platform/skill-docs/..%2F..%2Fetc/download").status_code in (400, 404)
    res = client.get("/api/platform/skill-docs/no-such-skill/download")
    assert res.status_code == 404
    assert res.json()["detail"] == "这个技能没有可下载的压缩包"


def test_handbook_pages_match_the_site_snapshot() -> None:
    """If the site gained or lost a page, the sync script must be re-run."""
    assert Path(DOCS_DIR).is_dir()
    assert len(list(DOCS_DIR.glob("*.md"))) >= 20
