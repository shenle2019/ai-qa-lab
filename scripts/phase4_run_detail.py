"""Screenshot one failed run with its AI root cause."""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
URL = "http://127.0.0.1:8000/ui/#/api-automation"


def main() -> int:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector(".tab")
        page.wait_for_timeout(1200)

        select = page.locator("select").first
        for index, text in enumerate(select.locator("option").all_inner_texts()):
            if "执行验证项目" in text:
                select.select_option(index=index)
                break
        page.wait_for_timeout(1000)

        page.locator(".tabs .tab", has_text="执行记录").first.click()
        page.wait_for_timeout(1000)

        rows = page.locator("table tbody tr")
        target = None
        for index in range(rows.count()):
            row = rows.nth(index)
            if row.locator("button", has_text="AI 归因").count():
                target = row
                break
        if target is None:
            print("no failed run found")
            browser.close()
            return 1

        target.locator("button", has_text="AI 归因").first.click(timeout=8000)
        page.wait_for_timeout(6000)
        target.locator("button", has_text="详情").first.click(timeout=8000)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(SHOTS / "phase4-api-run-detail.png"), full_page=True)
        print("ok run detail")
        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
