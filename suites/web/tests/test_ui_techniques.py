"""Web UI cases: equivalence, boundary, error guessing and user scenarios."""

import json
from uuid import uuid4

import pytest

from libs.miniplaywright import expect


def _settle(page):
    page.evaluate(
        "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))",
        await_promise=True,
    )


def _go_tickets(page, sut):
    page.goto(sut + "/ui/#/tickets")
    expect(page.locator("h1")).to_have_text("工单管理")
    page.wait_for_selector(".toolbar")
    _settle(page)


def _open_modal(page):
    page.locator(".toolbar-actions button.btn").click()
    page.wait_for_selector(".modal")
    _settle(page)


def _fill(page, title, description="", priority="medium"):
    page.locator('input[placeholder="一句话描述问题"]').fill(title)
    if description:
        page.locator('textarea[placeholder="复现步骤、期望结果、实际结果"]').fill(description)
    if priority != "medium":
        page.evaluate(
            f"""(() => {{ const sel = document.querySelector('.modal select');
            sel.value = {json.dumps(priority)};
            sel.dispatchEvent(new Event('change', {{bubbles:true}}));
            return sel.value; }})()"""
        )


def _submit_ok(page, title):
    page.locator(".modal-actions button.btn:last-child").click()
    page.wait_for_function("!document.querySelector('.modal')")
    expect(page.locator("body")).to_contain_text(title)


def _create(page, sut, title=None, description="", priority="medium"):
    _go_tickets(page, sut)
    _open_modal(page)
    title = title or f"web {uuid4().hex[:8]}"
    _fill(page, title, description, priority)
    _submit_ok(page, title)
    return title


def _row(title: str) -> str:
    return f"[...document.querySelectorAll('tbody tr')].find(r => r.innerText.includes({json.dumps(title)}))"


def _set_filter(page, index, value):
    page.evaluate(
        f"""(() => {{ const sel = document.querySelectorAll('.filters select')[{index}];
        sel.value = {json.dumps(value)};
        sel.dispatchEvent(new Event('change', {{bubbles:true}}));
        return sel.value; }})()"""
    )
    _settle(page)


def _search(page, value):
    page.evaluate(
        f"""(() => {{ const input = document.querySelector('input.search');
        input.value = {json.dumps(value)};
        input.dispatchEvent(new Event('input', {{bubbles:true}}));
        return input.value; }})()"""
    )
    _settle(page)


def _set_row_select(page, title, index, value):
    page.evaluate(
        f"""(() => {{ const row = {_row(title)};
        if (!row) return false;
        const sel = row.querySelectorAll('select')[{index}];
        sel.value = {json.dumps(value)};
        sel.dispatchEvent(new Event('change', {{bubbles:true}}));
        return true; }})()"""
    )
    _settle(page)


def test_tickets_page_loads(page, sut):
    _go_tickets(page, sut)


def test_sidebar_has_nine_entries(page, sut):
    _go_tickets(page, sut)
    assert page.evaluate("document.querySelectorAll('.nav-item').length") == 9


def test_dashboard_has_four_stat_cards(page, sut):
    page.goto(sut + "/ui/#/")
    page.wait_for_selector(".stat-card")
    assert page.evaluate("document.querySelectorAll('.stat-card').length") >= 4


def test_dashboard_shows_total_label(page, sut):
    page.goto(sut + "/ui/#/")
    page.wait_for_selector(".stat-card")
    expect(page.locator("body")).to_contain_text("全部工单")


@pytest.mark.parametrize("priority", ["low", "medium", "high"])
def test_create_ticket_by_priority(page, sut, priority):
    title = f"prio {priority} {uuid4().hex[:6]}"
    _create(page, sut, title=title, priority=priority)


def test_create_with_description(page, sut):
    title = f"desc {uuid4().hex[:6]}"
    _create(page, sut, title=title, description="复现步骤：打开页面")


@pytest.mark.parametrize(
    "title",
    [
        "中文标题-打印机无法连接",
        "支付失败 🔥🧾",
        "特殊字符 <>&\"'",
    ],
)
def test_create_title_variants(page, sut, title):
    _create(page, sut, title=f"{title}-{uuid4().hex[:4]}")


def test_title_input_declares_200_limit(page, sut):
    _go_tickets(page, sut)
    _open_modal(page)
    maxlength = page.evaluate(
        "document.querySelector('input[placeholder=\"一句话描述问题\"]').getAttribute('maxlength')"
    )
    assert maxlength == "200"
    page.locator('input[placeholder="一句话描述问题"]').fill("x" * 250)
    page.locator(".modal-actions button.btn:last-child").click()
    page.wait_for_function("!!document.querySelector('.modal')")


def test_empty_title_shows_error(page, sut):
    _go_tickets(page, sut)
    _open_modal(page)
    page.locator(".modal-actions button.btn:last-child").click()
    page.wait_for_function("document.body.innerText.includes('标题不能为空')")
    assert page.evaluate("!!document.querySelector('.modal')")


def test_whitespace_title_shows_error(page, sut):
    _go_tickets(page, sut)
    _open_modal(page)
    page.locator('input[placeholder="一句话描述问题"]').fill("   ")
    page.locator(".modal-actions button.btn:last-child").click()
    page.wait_for_function("document.body.innerText.includes('标题不能为空')")


def test_cancel_modal(page, sut):
    _go_tickets(page, sut)
    _open_modal(page)
    page.locator(".modal-actions button.btn.ghost").click()
    page.wait_for_function("!document.querySelector('.modal')")


def test_search_filters_rows(page, sut):
    first = _create(page, sut, title=f"alpha {uuid4().hex[:6]}")
    second = _create(page, sut, title=f"beta {uuid4().hex[:6]}")
    _search(page, first)
    page.wait_for_function(f"!document.body.innerText.includes({json.dumps(second)})")
    expect(page.locator("body")).to_contain_text(first)


def test_status_filter(page, sut):
    title = _create(page, sut, title=f"status filter {uuid4().hex[:6]}")
    _set_row_select(page, title, 1, "closed")
    page.wait_for_function(
        f"(() => {{ const row = {_row(title)}; return row && row.querySelectorAll('select')[1].value === 'closed'; }})()"
    )
    _set_filter(page, 0, "closed")
    expect(page.locator("body")).to_contain_text(title)
    _set_filter(page, 0, "open")
    page.wait_for_function(f"!document.body.innerText.includes({json.dumps(title)})")


def test_priority_filter(page, sut):
    title = _create(page, sut, title=f"priority filter {uuid4().hex[:6]}", priority="low")
    _set_filter(page, 1, "high")
    page.wait_for_function(f"!document.body.innerText.includes({json.dumps(title)})")
    _set_filter(page, 1, "low")
    expect(page.locator("body")).to_contain_text(title)


def test_update_status_inline(page, sut):
    title = _create(page, sut, title=f"update status {uuid4().hex[:6]}")
    _set_row_select(page, title, 1, "in_progress")
    page.wait_for_function(
        f"(() => {{ const row = {_row(title)}; return row && row.querySelectorAll('select')[1].value === 'in_progress'; }})()"
    )


def test_update_priority_inline(page, sut):
    title = _create(page, sut, title=f"update priority {uuid4().hex[:6]}", priority="medium")
    _set_row_select(page, title, 0, "high")
    page.wait_for_function(
        f"(() => {{ const row = {_row(title)}; return row && row.querySelectorAll('select')[0].value === 'high'; }})()"
    )


def test_delete_ticket(page, sut):
    title = _create(page, sut, title=f"delete {uuid4().hex[:6]}")
    page.evaluate("window.confirm = () => true")
    page.evaluate(
        f"""(() => {{ const row = {_row(title)};
        if (!row) return false;
        row.querySelector('button.delete-ticket').click();
        return true; }})()"""
    )
    page.wait_for_function(f"!document.body.innerText.includes({json.dumps(title)})")


def test_data_persists_after_reload(page, sut):
    title = _create(page, sut, title=f"persist {uuid4().hex[:6]}")
    page.goto(sut + "/ui/#/tickets")
    page.wait_for_selector(".toolbar")
    expect(page.locator("body")).to_contain_text(title)


@pytest.mark.parametrize(
    ("route", "heading"),
    [
        ("/ui/#/platform", "测试平台"),
        ("/ui/#/models", "模型中心"),
        ("/ui/#/report", "项目报告"),
        ("/ui/#/portfolio", "模块验收"),
        ("/ui/#/methodology", "方法论"),
        ("/ui/#/knowledge", "知识库问答"),
    ],
)
def test_navigation_pages(page, sut, route, heading):
    page.goto(sut + route)
    expect(page.locator("h1")).to_have_text(heading)
