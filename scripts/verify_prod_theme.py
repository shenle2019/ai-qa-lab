"""Confirm the deployed console serves the latest build."""

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://ai-qa-lab-production.up.railway.app/ui/"
OUT = Path("docs/ui-v4")

JS = """
() => ({
  groups: Array.from(document.querySelectorAll('.nav-group .nav-group-title'))
    .map(el => el.textContent.trim()).join(','),
  bg: getComputedStyle(document.body).backgroundColor,
  accent: getComputedStyle(document.documentElement).getPropertyValue('--accent').trim(),
})
"""


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE + "#/overview", wait_until="load")
        page.wait_for_timeout(2500)
        print(page.evaluate(JS))
        page.screenshot(path=str(OUT / "prod-v4-overview.png"), full_page=True)
        print("pageerrors", len(errors))
        browser.close()


if __name__ == "__main__":
    main()
