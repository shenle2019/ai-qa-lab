"""Phase 2 visual check: case management table, batch bar, edit modal, AI generation tab."""

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

        page.goto(BASE + "/functional", wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(OUT, "phase2-case-manage.png"), full_page=True)
        print("ok manage")

        boxes = page.locator("tbody tr td.check-col input")
        if boxes.count() >= 2:
            boxes.nth(0).check()
            boxes.nth(1).check()
            page.wait_for_timeout(300)
            page.screenshot(path=os.path.join(OUT, "phase2-case-batch.png"), full_page=True)
            print("ok batch bar")

            page.locator("button.btn.ghost", has_text="编辑").first.click()
            page.wait_for_timeout(400)
            page.screenshot(path=os.path.join(OUT, "phase2-case-edit.png"), full_page=True)
            print("ok edit modal")
            page.keyboard.press("Escape")
            page.locator(".modal header button").click()
            page.wait_for_timeout(200)
        else:
            print("not enough rows for batch/edit shots")

        page.locator(".tab", has_text="AI 生成").click()
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(OUT, "phase2-case-generate.png"), full_page=True)
        print("ok generate tab")

        with open(os.path.join(OUT, "phase2-text.txt"), "w", encoding="utf-8") as fh:
            fh.write(page.inner_text("body"))
        browser.close()

    if errors:
        print("PAGE ERRORS:")
        for item in errors:
            print(item)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
