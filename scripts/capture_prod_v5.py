"""Capture the deployed console for the current palette."""

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://ai-qa-lab-production.up.railway.app/ui/"
OUT = Path("docs/ui-v5")
PAGES = [("overview", "#/overview"), ("functional", "#/functional"), ("api", "#/api-automation")]

JS = """
() => ({bg: getComputedStyle(document.body).backgroundColor,
        accent: getComputedStyle(document.documentElement).getPropertyValue('--accent').trim(),
        groups: Array.from(document.querySelectorAll('.nav-group-title')).map(e => e.textContent.trim()).join(',')})
"""


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        for name, path in PAGES:
            page.goto(BASE + path, wait_until="load")
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:  # noqa: BLE001 - production can stay busy
                pass
            page.wait_for_timeout(2500)
            page.screenshot(path=str(OUT / f"prod-v5-{name}.png"), full_page=True)
        print(page.evaluate(JS))
        print("pageerrors", len(errors))
        browser.close()


if __name__ == "__main__":
    main()
