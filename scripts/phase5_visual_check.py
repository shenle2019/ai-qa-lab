"""Screenshot the UI automation page across its three tabs."""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
URL = "http://127.0.0.1:8000/ui/#/ui-automation"


def main() -> int:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors: list[str] = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector(".tab")
        page.wait_for_timeout(1200)

        select = page.locator(".toolbar select").first
        for index, text in enumerate(select.locator("option").all_inner_texts()):
            if "执行验证项目" in text:
                select.select_option(index=index)
                break
        page.wait_for_timeout(900)
        page.screenshot(path=str(SHOTS / "phase5-ui-explore.png"), full_page=True)
        print("ok explore")

        page.locator(".tabs .tab", has_text="UI 用例").first.click()
        page.wait_for_timeout(900)
        page.screenshot(path=str(SHOTS / "phase5-ui-cases.png"), full_page=True)
        print("ok cases")

        page.locator(".tabs .tab", has_text="执行记录").first.click()
        page.wait_for_timeout(900)
        page.screenshot(path=str(SHOTS / "phase5-ui-runs.png"), full_page=True)
        print("ok runs")

        detail = page.locator("table button", has_text="详情").first
        if detail.count():
            detail.click()
            page.wait_for_timeout(900)
            page.screenshot(path=str(SHOTS / "phase5-ui-run-detail.png"), full_page=True)
            print("ok run detail")
            page.locator(".modal header .btn", has_text="关闭").first.click()
            page.wait_for_timeout(400)

        page.locator(".tabs .tab", has_text="UI 用例").first.click()
        page.wait_for_timeout(800)
        edit = page.locator("table button", has_text="编辑").first
        if edit.count():
            edit.click()
            page.wait_for_timeout(800)
            page.screenshot(path=str(SHOTS / "phase5-ui-case-edit.png"), full_page=True)
            print("ok edit")
            page.locator(".modal header .btn", has_text="关闭").first.click()
            page.wait_for_timeout(400)
            script = page.locator("table button", has_text="脚本").first
            script.click()
            page.wait_for_timeout(900)
            page.screenshot(path=str(SHOTS / "phase5-ui-case-script.png"), full_page=True)
            print("ok script")

        if errors:
            print("pageerror:", errors[:2])
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
