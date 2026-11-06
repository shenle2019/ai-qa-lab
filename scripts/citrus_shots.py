"""Screenshot the Citrus Lab pass for review."""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("UI_BASE", "http://127.0.0.1:8000/ui/")
OUT = Path(os.environ.get("UI_SHOT_DIR", "docs/ui-citrus"))
PAGES = [
    ("projects", "#/projects"),
    ("overview", "#/overview"),
    ("requirements", "#/requirements"),
    ("functional", "#/functional"),
    ("kb", "#/kb"),
    ("api", "#/api-automation"),
    ("ui", "#/ui-automation"),
    ("users", "#/users"),
    ("system-ai", "#/system-ai"),
]


def launch(playwright):
    """Use the bundled headless shell when present, else a locally installed Chrome."""
    channel = os.environ.get("UI_SHOT_CHANNEL", "chrome")
    try:
        return playwright.chromium.launch()
    except Exception:
        return playwright.chromium.launch(channel=channel)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        for name, path in PAGES:
            page.goto(BASE + path, wait_until="load")
            page.wait_for_timeout(1600)
            page.screenshot(path=str(OUT / f"citrus-{name}.png"), full_page=True)
        print("pages", len(PAGES), "pageerrors", len(errors))
        browser.close()


if __name__ == "__main__":
    main()
