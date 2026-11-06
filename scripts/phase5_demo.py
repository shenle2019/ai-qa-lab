"""Reset Phase 5 demo data, then drive explore + run from the real UI."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
BASE = "http://127.0.0.1:8000/api/platform"
PAGE = "http://127.0.0.1:8000/ui/#/ui-automation"

GOAL = "打开知识库页面，确认页面上出现「试检索」入口"


def cleanup() -> None:
    client = httpx.Client(timeout=30)
    cases = client.get(f"{BASE}/ui-cases", params={"project_id": 2}).json()
    for item in cases:
        client.delete(f"{BASE}/ui-cases/{item['id']}")
    runs = client.get(f"{BASE}/ui-runs", params={"project_id": 2}).json()
    print("removed cases", len(cases), "runs left", len(runs))


def main() -> int:
    cleanup()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1050})
        page.goto(PAGE, wait_until="networkidle")
        page.wait_for_selector(".tab")
        page.wait_for_timeout(1000)

        select = page.locator(".toolbar select").first
        for index, text in enumerate(select.locator("option").all_inner_texts()):
            if "执行验证项目" in text:
                select.select_option(index=index)
                break
        page.wait_for_timeout(600)

        page.fill("input[placeholder^='http']", "http://127.0.0.1:8000/ui/#/kb")
        page.fill("textarea[placeholder^='例如']", GOAL)
        page.locator("button", has_text="AI 生成用例").first.click()
        page.wait_for_timeout(45000)
        page.screenshot(path=str(SHOTS / "phase5-ui-explore.png"), full_page=True)
        print("ok explore with result")

        page.locator(".tabs .tab", has_text="UI 用例").first.click()
        page.wait_for_timeout(1200)
        page.screenshot(path=str(SHOTS / "phase5-ui-cases.png"), full_page=True)
        print("ok cases")

        run_button = page.locator("table button", has_text="执行").first
        run_button.click()
        page.wait_for_timeout(20000)
        page.screenshot(path=str(SHOTS / "phase5-ui-cases.png"), full_page=True)

        page.locator(".tabs .tab", has_text="执行记录").first.click()
        page.wait_for_timeout(1200)
        page.screenshot(path=str(SHOTS / "phase5-ui-runs.png"), full_page=True)
        print("ok runs")

        detail = page.locator("table button", has_text="详情").first
        if detail.count():
            detail.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=str(SHOTS / "phase5-ui-run-detail.png"), full_page=True)
            print("ok run detail")
            page.locator(".modal header .btn", has_text="关闭").first.click()
            page.wait_for_timeout(400)

        page.locator(".tabs .tab", has_text="UI 用例").first.click()
        page.wait_for_timeout(900)
        page.locator("table button", has_text="编辑").first.click()
        page.wait_for_timeout(900)
        page.screenshot(path=str(SHOTS / "phase5-ui-case-edit.png"), full_page=True)
        print("ok edit")
        page.locator(".modal header .btn", has_text="关闭").first.click()
        page.wait_for_timeout(400)
        page.locator("table button", has_text="脚本").first.click()
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SHOTS / "phase5-ui-case-script.png"), full_page=True)
        print("ok script")
        browser.close()

    client = httpx.Client(timeout=30)
    final_cases = client.get(f"{BASE}/ui-cases", params={"project_id": 2}).json()
    final_runs = client.get(f"{BASE}/ui-runs", params={"project_id": 2}).json()
    print("cases", [(c["id"], c["source"], len(c["steps"])) for c in final_cases])
    print("runs", [(r["id"], r["status"], r["duration_ms"]) for r in final_runs])
    return 0


if __name__ == "__main__":
    sys.exit(main())
