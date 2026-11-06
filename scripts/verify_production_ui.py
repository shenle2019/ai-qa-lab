"""Screenshot the deployed UI and check the response of key pages."""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://ai-qa-lab-production.up.railway.app/ui/#"
OUT = Path(__file__).resolve().parents[1] / "docs" / "explore" / "2026-11-06-exploratory" / "shots"

PAGES = [
    ("overview", "/overview", "prod-overview.png"),
    ("projects", "/projects", "prod-projects.png"),
    ("requirements", "/requirements", "prod-requirements.png"),
    ("api", "/api-automation", "prod-api.png"),
    ("ui", "/ui-automation", "prod-ui.png"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        for name, path, shot in PAGES:
            page.goto(f"{BASE}{path}", wait_until="networkidle")
            page.wait_for_timeout(1200)
            title = page.locator("h1").first.inner_text()
            page.screenshot(path=str(OUT / shot), full_page=True)
            print(f"ok {name} :: h1={title}")

        page.goto(f"{BASE}/ui-automation", wait_until="networkidle")
        page.wait_for_timeout(800)
        body = page.locator("body").inner_text()
        print("playwright banner:", "没有安装 Playwright" in body)
        print("docs button:", page.locator("a, button", has_text="API 文档").count())

        browser.close()

    print("console errors:", len(errors))
    for item in errors[:5]:
        print(" -", item)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
