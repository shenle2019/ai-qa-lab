from libs.miniplaywright import expect


def test_goto_and_title(page, html_url):
    page.goto(html_url)
    assert page.title() == "miniplaywright fixture"
    expect(page).to_have_url("page.html")


def test_click(page, html_url):
    page.goto(html_url)
    page.locator("#btn").click()
    expect(page.locator("#out")).to_have_text("clicked")


def test_fill_dispatches_input(page, html_url):
    page.goto(html_url)
    page.locator("#name").fill("alice")
    expect(page.locator("#echo")).to_have_text("alice")


def test_expect_visible_and_count(page, html_url):
    page.goto(html_url)
    expect(page.locator("#title")).to_be_visible()
    expect(page.locator("li")).to_have_count(2)
    expect(page.locator("#title")).to_contain_text("Hell")


def test_auto_wait_for_delayed_text(page, html_url):
    page.goto(html_url)
    expect(page.locator("#delayed")).to_have_text("ready", timeout=3)


def test_screenshot(page, html_url, tmp_path):
    page.goto(html_url)
    target = page.screenshot(tmp_path / "shot.png")
    assert target.exists()
    assert target.stat().st_size > 1000
