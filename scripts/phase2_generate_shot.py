"""Phase 2 UI generation shot: drive the AI generation tab and capture the preview."""

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
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        page.goto(BASE + "/functional", wait_until="networkidle")
        page.wait_for_timeout(1500)
        if errors:
            print("PAGE ERRORS BEFORE CLICK:", errors)
        page.screenshot(path=os.path.join(OUT, "phase2-debug-before.png"), full_page=False)
        with open(os.path.join(OUT, "phase2-debug-before.txt"), "w", encoding="utf-8") as fh:
            fh.write(page.inner_text("body"))
        try:
            page.wait_for_selector(".tab", timeout=8000)
        except Exception:  # noqa: BLE001
            print("no .tab element; body text saved")
            browser.close()
            return 1
        page.locator(".tabs .tab").nth(1).click()
        page.wait_for_timeout(500)

        select = page.locator(".form-stack select").nth(1)
        options = select.locator("option")
        chosen = None
        for index in range(options.count()):
            text = options.nth(index).inner_text()
            if "不使用需求库" not in text:
                chosen = index
                break
        if chosen is None:
            print("no requirement option available")
            browser.close()
            return 1
        select.select_option(index=chosen)
        page.wait_for_timeout(300)

        page.locator("button", has_text="AI 生成用例").click()
        page.wait_for_timeout(1000)
        for _ in range(60):
            text = page.inner_text("body")
            if "生成中" not in text:
                break
            page.wait_for_timeout(1000)
        page.wait_for_timeout(1200)

        page.screenshot(path=os.path.join(OUT, "phase2-case-generate-result.png"), full_page=True)
        body = page.inner_text("body")
        print("preview has draft:", "草稿" in body or "draft" in body)
        print(body[-800:])

        browser.close()

    if errors:
        print("PAGE ERRORS:")
        for item in errors:
            print(item)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
