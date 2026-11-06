"""Screenshot the Phase 5 admin pages: system AI, modules, members, AI logs."""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
UI = "http://127.0.0.1:8000/ui/#"

PAGES = [
    ("system-ai", "/system-ai", "phase5-system-ai.png"),
    ("modules", "/modules", "phase5-modules.png"),
    ("members", "/members", "phase5-members.png"),
    ("users", "/users", "phase5-users.png"),
    ("ai-logs", "/ai-logs", "phase5-ai-logs.png"),
]


def main() -> int:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1020})
        errors: list[str] = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        for key, path, shot in PAGES:
            page.goto(UI + path, wait_until="networkidle")
            page.wait_for_timeout(1100)
            if key in ("modules", "members"):
                select = page.locator(".toolbar select").first
                for index, text in enumerate(select.locator("option").all_inner_texts()):
                    if "执行验证项目" in text:
                        select.select_option(index=index)
                        break
                page.wait_for_timeout(900)
            page.screenshot(path=str(SHOTS / shot), full_page=True)
            print("ok", key)

        # System AI: switch to the embedding tab
        page.goto(UI + "/system-ai", wait_until="networkidle")
        page.wait_for_timeout(900)
        page.locator(".tabs .tab", has_text="向量模型配置").first.click()
        page.wait_for_timeout(900)
        page.screenshot(path=str(SHOTS / "phase5-system-ai-embedding.png"), full_page=True)
        print("ok system-ai-embedding")

        page.locator(".tabs .tab", has_text="Midscene").first.click()
        page.wait_for_timeout(900)
        page.screenshot(path=str(SHOTS / "phase5-system-ai-midscene.png"), full_page=True)
        print("ok system-ai-midscene")

        if errors:
            print("pageerror:", errors[:3])
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
