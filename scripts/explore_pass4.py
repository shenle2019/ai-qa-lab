"""Exploratory pass 4: focus visibility, header buttons, cross-page navigation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs" / "explore" / "2026-11-06-exploratory"
SHOTS = DIR / "shots"
UI = "http://127.0.0.1:8000/ui/#"


def main() -> int:
    notes: list[dict] = []

    def add(probe: str, text: str) -> None:
        notes.append({"probe": probe, "observation": text})
        print(f"[{probe}] {text.encode('ascii', 'replace').decode()[:150]}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        # 1. focus ring on first interactive element
        page.goto(UI + "/projects", wait_until="networkidle")
        page.wait_for_timeout(600)
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        page.wait_for_timeout(300)
        page.screenshot(path=str(SHOTS / "focus-second-tab.png"))
        info = page.evaluate(
            """() => {
            const el = document.activeElement;
            const cs = getComputedStyle(el);
            return {tag: el.tagName, cls: el.className, outline: cs.outline, shadow: cs.boxShadow};
        }"""
        )
        add("focus-ring", json.dumps(info, ensure_ascii=False))

        # 2. header 刷新状态
        page.locator("button", has_text="刷新状态").first.click()
        page.wait_for_timeout(900)
        add("refresh-status", "clicked; alert=" + (page.locator(".alert").first.inner_text()[:60] if page.locator(".alert").count() else "none"))

        # 3. project row 生成用例 navigation
        gen = page.locator("table button", has_text="生成用例").first
        if gen.count():
            gen.click()
            page.wait_for_timeout(1200)
            add("project-generate-case", f"hash={page.evaluate('location.hash')}")
            page.goto(UI + "/projects", wait_until="networkidle")
            page.wait_for_timeout(600)

        # 4. project row 概览 navigation
        ov = page.locator("table button", has_text="概览").first
        if ov.count():
            ov.click()
            page.wait_for_timeout(1000)
            add("project-overview-nav", f"hash={page.evaluate('location.hash')} hero={page.inner_text('.hero h2')[:20] if page.locator('.hero h2').count() else '-'}")
            page.screenshot(path=str(SHOTS / "project-overview-from-row.png"))

        # 5. empty requirement list guidance
        page.goto(UI + "/requirements", wait_until="networkidle")
        page.wait_for_timeout(900)
        body = page.inner_text("body")
        add("requirements-empty-guidance", f"has_新建={('新建需求' in body)} has_空态={page.locator('.empty').count()} first_rows={page.locator('table tbody tr').count()}")

        # 6. environments placeholder content
        page.goto(UI + "/environments", wait_until="networkidle")
        page.wait_for_timeout(700)
        add("environments", page.inner_text(".module-planned")[:200].replace("\n", " / ") if page.locator(".module-planned").count() else "no placeholder block")
        page.screenshot(path=str(SHOTS / "environments.png"))

        browser.close()

    (DIR / "pass4.json").write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
