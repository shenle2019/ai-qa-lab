from pathlib import Path
from uuid import uuid4

from libs.miniplaywright import expect
from libs.minipytest import mark

ROOT = Path(__file__).resolve().parents[3]
SHOTS = ROOT / "docs" / "portfolio" / "screenshots"


@mark.smoke
def test_dashboard_loads(page):
    expect(page).to_have_title("AI全栈测试开发平台-shenle · Knowledge Ops")
    expect(page.locator("h1")).to_have_text("仪表盘")
    expect(page.locator(".stats-grid")).to_be_visible()
    page.screenshot(SHOTS / "module-04-dashboard.png")


def test_tickets_page(page, sut):
    page.goto(sut + "/ui/#/tickets")
    expect(page.locator("h1")).to_have_text("工单管理")
    expect(page.locator(".toolbar")).to_be_visible()


def test_create_ticket_via_ui(page, sut):
    page.goto(sut + "/ui/#/tickets")
    expect(page.locator("h1")).to_have_text("工单管理")

    page.locator(".toolbar-actions button.btn").click()
    page.wait_for_selector(".modal")

    title = f"miniplaywright {uuid4().hex[:8]}"
    page.locator('input[placeholder="一句话描述问题"]').fill(title)
    page.locator('textarea[placeholder="复现步骤、期望结果、实际结果"]').fill(
        "created by miniplaywright"
    )
    page.locator(".modal-actions button.btn:last-child").click()
    page.wait_for_function("!document.querySelector('.modal')", timeout=10)

    expect(page.locator("body")).to_contain_text(title)
    page.screenshot(SHOTS / "module-04-tickets.png")


def test_workbench_page(page, sut):
    page.goto(sut + "/ui/#/workbench")
    expect(page.locator("h1")).to_have_text("API 工作台")
    expect(page.locator(".workbench-grid")).to_be_visible()


def test_portfolio_page(page, sut):
    page.goto(sut + "/ui/#/portfolio")
    expect(page.locator("h1")).to_have_text("模块验收")
    expect(page.locator("body")).to_contain_text("Python 测试开发")
