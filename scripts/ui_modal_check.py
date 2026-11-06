"""Open a few modals and drawers to check they follow the light theme."""

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000/ui/"
OUT = Path("docs/ui-v4")


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        page.goto(BASE + "#/requirements", wait_until="load")
        page.wait_for_timeout(1500)
        page.locator("button", has_text="新建需求").first.click()
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT / "v4-modal-requirement.png"))
        print("requirement modal ok")

        page.keyboard.press("Escape")
        page.wait_for_timeout(400)

        page.goto(BASE + "#/api-automation", wait_until="load")
        page.wait_for_timeout(1500)
        page.locator(".tabs .tab", has_text="接口管理").first.click()
        page.wait_for_timeout(700)
        page.locator("table button", has_text="调试").first.click()
        page.wait_for_timeout(900)
        page.screenshot(path=str(OUT / "v4-drawer-debug.png"), full_page=True)
        print("debug drawer ok")

        browser.close()


if __name__ == "__main__":
    main()
