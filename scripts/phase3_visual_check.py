"""Phase 3 visual check: knowledge base list, retrieval trial and chunk viewer."""

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
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        page.goto(BASE + "/kb", wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(OUT, "phase3-kb-overview.png"), full_page=True)
        print("ok overview")

        page.locator(".search-bar input").fill("导出超过 5000 条会怎么处理")
        page.locator(".search-bar button").click()
        page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(OUT, "phase3-kb-search.png"), full_page=True)
        print("ok search")

        page.locator("tbody tr button", has_text="分块").first.click()
        page.wait_for_timeout(900)
        page.screenshot(path=os.path.join(OUT, "phase3-kb-chunks.png"), full_page=True)
        print("ok chunks")

        with open(os.path.join(OUT, "phase3-text.txt"), "w", encoding="utf-8") as fh:
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
