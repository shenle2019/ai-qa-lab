import json
from uuid import uuid4

from libs.miniplaywright import expect


def _go_tickets(page, sut):
    page.goto(sut + "/ui/#/tickets")
    expect(page.locator("h1")).to_have_text("工单管理")
    page.wait_for_selector(".toolbar")


def _open_modal(page):
    page.locator(".toolbar-actions button.btn").click()
    page.wait_for_selector(".modal")


def _fill_form(page, title, description="", priority="medium"):
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


def _submit(page, title):
    page.locator(".modal-actions button.btn:last-child").click()
    page.wait_for_function("!document.querySelector('.modal')")
    expect(page.locator("body")).to_contain_text(title)


def _create(page, sut, title=None, description="", priority="medium"):
    _go_tickets(page, sut)
    _open_modal(page)
    title = title or f"web {uuid4().hex[:8]}"
    _fill_form(page, title, description, priority)
    _submit(page, title)
    return title


def _row_js(title: str) -> str:
    return f"[...document.querySelectorAll('tbody tr')].find(r => r.innerText.includes({json.dumps(title)}))"


def _wait_row_contains(page, title, text, timeout=5):
    page.wait_for_function(
        f"(() => {{ const row = {_row_js(title)}; return !!row && row.innerText.includes({json.dumps(text)}); }})()",
        timeout=timeout,
    )


def _wait_row_select(page, title, index, value, timeout=5):
    page.wait_for_function(
        f"(() => {{ const row = {_row_js(title)}; return !!row && row.querySelectorAll('select')[{index}].value === {json.dumps(value)}; }})()",
        timeout=timeout,
    )


def _set_row_select(page, title, index, value):
    page.evaluate(
        f"""(() => {{ const row = {_row_js(title)};
        if (!row) return false;
        const sel = row.querySelectorAll('select')[{index}];
        sel.value = {json.dumps(value)};
        sel.dispatchEvent(new Event('change', {{bubbles:true}}));
        return true; }})()"""
    )


def _delete_row(page, title):
    page.evaluate("window.confirm = () => true")
    page.evaluate(
        f"""(() => {{ const row = {_row_js(title)};
        if (!row) return false;
        row.querySelector('button.delete-ticket').click();
        return true; }})()"""
    )
    page.wait_for_function(
        f"(() => !document.body.innerText.includes({json.dumps(title)}))()",
        timeout=5,
    )


def test_tickets_page_loads(page, sut):
    _go_tickets(page, sut)
    expect(page.locator(".toolbar")).to_be_visible()


def test_create_minimal_ticket(page, sut):
    title = _create(page, sut)
    expect(page.locator("body")).to_contain_text(title)


def test_create_ticket_with_description(page, sut):
    title = _create(page, sut, description="created in web crud suite")
    expect(page.locator("body")).to_contain_text(title)


def test_create_high_priority_ticket(page, sut):
    title = _create(page, sut, priority="high")
    _wait_row_select(page, title, 0, "high")


def test_create_low_priority_ticket(page, sut):
    title = _create(page, sut, priority="low")
    _wait_row_select(page, title, 0, "low")


def test_create_second_ticket(page, sut):
    first = _create(page, sut)
    second = _create(page, sut)
    expect(page.locator("body")).to_contain_text(first)
    expect(page.locator("body")).to_contain_text(second)


def test_cancel_modal(page, sut):
    _go_tickets(page, sut)
    _open_modal(page)
    page.locator(".modal-actions button.btn.ghost").click()
    page.wait_for_function("!document.querySelector('.modal')")


def test_empty_title_shows_error(page, sut):
    _go_tickets(page, sut)
    _open_modal(page)
    page.locator(".modal-actions button.btn:last-child").click()
    expect(page.locator(".modal")).to_contain_text("标题不能为空")


def test_long_title_200(page, sut):
    title = "x" * 200
    _create(page, sut, title=title)
    expect(page.locator("body")).to_contain_text(title)


def test_created_ticket_visible(page, sut):
    title = _create(page, sut)
    page.goto(sut + "/ui/#/tickets")
    expect(page.locator("body")).to_contain_text(title)


def test_update_status_in_progress(page, sut):
    title = _create(page, sut)
    _set_row_select(page, title, 1, "in_progress")
    _wait_row_contains(page, title, "处理中")


def test_update_status_closed(page, sut):
    title = _create(page, sut)
    _set_row_select(page, title, 1, "closed")
    _wait_row_contains(page, title, "已关闭")


def test_update_priority_high(page, sut):
    title = _create(page, sut)
    _set_row_select(page, title, 0, "high")
    _wait_row_select(page, title, 0, "high")


def test_update_priority_low(page, sut):
    title = _create(page, sut)
    _set_row_select(page, title, 0, "low")
    _wait_row_select(page, title, 0, "low")


def test_update_status_and_priority(page, sut):
    title = _create(page, sut)
    _set_row_select(page, title, 1, "in_progress")
    _set_row_select(page, title, 0, "high")
    _wait_row_contains(page, title, "处理中")
    _wait_row_select(page, title, 0, "high")


def test_delete_ticket(page, sut):
    title = _create(page, sut)
    _delete_row(page, title)


def test_delete_second_ticket(page, sut):
    _create(page, sut)
    title = _create(page, sut)
    _delete_row(page, title)


def test_deleted_ticket_not_in_search(page, sut):
    title = _create(page, sut)
    _delete_row(page, title)
    page.evaluate(
        f"""(() => {{ const input = document.querySelector('.filters .search');
        input.value = {json.dumps(title)};
        input.dispatchEvent(new Event('input', {{bubbles:true}})); }})()"""
    )
    page.wait_for_function(
        f"(() => !document.body.innerText.includes({json.dumps(title)}))()",
        timeout=5,
    )


def test_search_filters_title(page, sut):
    first = _create(page, sut)
    second = _create(page, sut)
    page.evaluate(
        f"""(() => {{ const input = document.querySelector('.filters .search');
        input.value = {json.dumps(first)};
        input.dispatchEvent(new Event('input', {{bubbles:true}})); }})()"""
    )
    page.wait_for_function(
        f"(() => document.body.innerText.includes({json.dumps(first)}) && !document.body.innerText.includes({json.dumps(second)}))()",
        timeout=5,
    )


def test_status_filter_closed(page, sut):
    open_title = _create(page, sut)
    closed_title = _create(page, sut)
    _set_row_select(page, closed_title, 1, "closed")
    _wait_row_contains(page, closed_title, "已关闭")
    page.evaluate(
        """(() => { const sel = document.querySelectorAll('.filters select')[0];
        sel.value = 'closed'; sel.dispatchEvent(new Event('change', {bubbles:true})); })()"""
    )
    page.wait_for_function(
        f"(() => !document.body.innerText.includes({json.dumps(open_title)}))()",
        timeout=5,
    )


def test_priority_filter_high(page, sut):
    low_title = _create(page, sut, priority="low")
    high_title = _create(page, sut, priority="high")
    page.evaluate(
        """(() => { const sel = document.querySelectorAll('.filters select')[1];
        sel.value = 'high'; sel.dispatchEvent(new Event('change', {bubbles:true})); })()"""
    )
    page.wait_for_function(
        f"(() => !document.body.innerText.includes({json.dumps(low_title)}))()",
        timeout=5,
    )
    expect(page.locator("body")).to_contain_text(high_title)


def test_navigate_workbench(page, sut):
    page.goto(sut + "/ui/#/workbench")
    expect(page.locator("h1")).to_have_text("API 工作台")


def test_navigate_knowledge(page, sut):
    page.goto(sut + "/ui/#/knowledge")
    expect(page.locator("h1")).to_have_text("知识库问答")


def test_navigate_report(page, sut):
    page.goto(sut + "/ui/#/report")
    expect(page.locator("h1")).to_have_text("项目报告")


def test_navigate_portfolio(page, sut):
    page.goto(sut + "/ui/#/portfolio")
    expect(page.locator("h1")).to_have_text("模块验收")


def test_navigate_platform(page, sut):
    page.goto(sut + "/ui/#/platform")
    expect(page.locator("h1")).to_have_text("测试平台")
    expect(page.locator(".platform-columns")).to_be_visible()


def test_navigate_methodology(page, sut):
    page.goto(sut + "/ui/#/methodology")
    expect(page.locator("h1")).to_have_text("方法论")
    expect(page.locator("body")).to_contain_text("分层选型决策树")


def test_dashboard_loads_after_create(page, sut):
    title = _create(page, sut)
    page.goto(sut + "/ui/")
    expect(page.locator("h1")).to_have_text("仪表盘")
    expect(page.locator("body")).to_contain_text(title)
