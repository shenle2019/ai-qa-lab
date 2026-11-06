"""Phase 0 visual check: screenshot the rebuilt shell and its new pages."""

import sys

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000/ui/#"
OUT = r"E:\ailearning\ai-qa-lab\docs\screenshots"

PAGES = [
    ("/", "phase0-overview.png"),
    ("/projects", "phase0-projects.png"),
    ("/system-ai", "phase0-system-ai.png"),
    ("/functional", "phase0-functional.png"),
    ("/requirements", "phase0-requirements.png"),
    ("/api-automation", "phase0-api-automation.png"),
]


def main() -> int:
    import os

    os.makedirs(OUT, exist_ok=True)
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        for path, name in PAGES:
            page.goto(BASE + path, wait_until="networkidle")
            page.wait_for_timeout(600)
            page.screenshot(path=os.path.join(OUT, name), full_page=True)
            print(f"ok {path} -> {name}")
        nav_text = page.inner_text(".sidebar")
        with open(os.path.join(OUT, "phase0-sidebar.txt"), "w", encoding="utf-8") as fh:
            fh.write(nav_text)
        print("sidebar dumped")
        browser.close()
    if errors:
        print("PAGE ERRORS:")
        for item in errors:
            print(item)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
