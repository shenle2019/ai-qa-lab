"""Screenshot the production console with an API key so the data is real."""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://ai-qa-lab-production.up.railway.app/ui/"
KEY = os.environ.get("PROD_API_KEY", "")
OUT = Path("docs/ui-citrus/prod")
PAGES = [
    ("projects", "#/projects"),
    ("overview", "#/overview"),
    ("functional", "#/functional"),
    ("kb", "#/kb"),
    ("api", "#/api-automation"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        if KEY:
            context.add_init_script(
                f"""() => {{
                  try {{ localStorage.setItem('sut_api_key', {KEY!r}) }} catch (e) {{}}
                }}"""
            )
        page = context.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        for name, path in PAGES:
            page.goto(BASE + path, wait_until="load")
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:  # noqa: BLE001
                pass
            page.wait_for_timeout(2600)
            page.screenshot(path=str(OUT / f"citrus-{name}.png"), full_page=True)
        print("pages", len(PAGES), "pageerrors", len(errors))
        browser.close()


if __name__ == "__main__":
    main()
