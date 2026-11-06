"""Phase 1 visual check: requirement list, detail with analysis, plan tab, chat."""

import os
import sys

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000/ui/#"
OUT = r"E:\ailearning\ai-qa-lab\docs\screenshots"


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        page.goto(BASE + "/requirements", wait_until="networkidle")
        page.wait_for_timeout(900)
        page.screenshot(path=os.path.join(OUT, "phase1-requirements-list.png"), full_page=True)
        print("ok list")

        rows = page.locator("tbody tr").count()
        if rows == 0:
            print("no requirement rows; nothing to open")
            with open(os.path.join(OUT, "phase1-requirements-text.txt"), "w", encoding="utf-8") as fh:
                fh.write(page.inner_text("main, .content, body"))
            browser.close()
            return 0

        page.locator("button.link").first.click()
        page.wait_for_selector(".detail-grid", timeout=15000)
        page.wait_for_timeout(700)
        page.screenshot(path=os.path.join(OUT, "phase1-requirement-detail.png"), full_page=True)
        print("ok detail")

        page.locator(".tab", has_text="测试计划").click()
        page.wait_for_timeout(400)
        page.screenshot(path=os.path.join(OUT, "phase1-requirement-plan.png"), full_page=True)
        print("ok plan")

        page.locator(".tab", has_text="待澄清").click()
        page.wait_for_timeout(400)
        page.screenshot(path=os.path.join(OUT, "phase1-requirement-clarify.png"), full_page=True)
        print("ok clarify")

        with open(os.path.join(OUT, "phase1-requirements-text.txt"), "w", encoding="utf-8") as fh:
            fh.write(page.inner_text("body"))
        print("text dumped")
        browser.close()

    if errors:
        print("PAGE ERRORS:")
        for item in errors:
            print(item)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
