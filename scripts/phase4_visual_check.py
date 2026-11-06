"""Screenshot every API automation tab (Phase 4 visual check)."""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
URL = "http://127.0.0.1:8000/ui/#/api-automation"

TABS = [
    ("接口管理", "phase4-api-endpoints"),
    ("接口资产", "phase4-api-assets"),
    ("单接口 Agent", "phase4-api-single-agent"),
    ("场景 Agent", "phase4-api-scenario-agent"),
    ("单接口用例", "phase4-api-cases"),
    ("接口场景", "phase4-api-scenarios"),
    ("执行记录", "phase4-api-runs"),
]


def main() -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors: list[str] = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector(".tab")
        page.wait_for_timeout(1200)

        # 项目下拉默认取第一个项目；这里显式切到有演示数据的「执行验证项目」。
        select = page.locator("select").first
        options = select.locator("option").all_inner_texts()
        for index, text in enumerate(options):
            if "执行验证项目" in text:
                select.select_option(index=index)
                page.wait_for_timeout(1200)
                break

        for label, name in TABS:
            masks = page.locator(".modal-mask")
            if masks.count():
                print("mask before", label, repr(masks.first.inner_text()[:120]))
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)
            tab = page.locator(".tabs .tab", has_text=label).first
            tab.click(timeout=10000)
            page.wait_for_timeout(900)
            page.screenshot(path=str(SHOTS / f"{name}.png"), full_page=True)
            print("ok", label)

        page.locator(".tabs .tab", has_text="执行记录").first.click()
        page.wait_for_timeout(900)
        try:
            page.locator("table button", has_text="AI 归因").first.click(timeout=8000)
            page.wait_for_timeout(2500)
            page.locator("table button", has_text="详情").first.click(timeout=8000)
            page.wait_for_timeout(1200)
            page.screenshot(path=str(SHOTS / "phase4-api-run-detail.png"), full_page=True)
            print("ok run detail")
        except Exception as exc:  # noqa: BLE001 - screenshot best effort
            print("run detail skipped:", exc.__class__.__name__)

        try:
            page.locator(".modal-mask button", has_text="关闭").first.click(timeout=5000)
        except Exception:  # noqa: BLE001
            page.keyboard.press("Escape")
        page.wait_for_timeout(600)

        page.locator(".tabs .tab", has_text="接口管理").first.click()
        page.wait_for_timeout(600)
        try:
            debug = page.locator("table button", has_text="调试")
            debug.first.click(timeout=8000)
            page.wait_for_timeout(900)
            page.screenshot(path=str(SHOTS / "phase4-api-debug.png"), full_page=True)
            print("ok debug drawer")
        except Exception as exc:  # noqa: BLE001
            print("debug drawer skipped:", exc.__class__.__name__)

        text = page.inner_text("body")
        (SHOTS / "phase4-text.txt").write_text(text, encoding="utf-8")
        browser.close()
        if errors:
            print("pageerror:", errors[:3])
        return 0


if __name__ == "__main__":
    sys.exit(main())
