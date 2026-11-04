from libs.miniplaywright import expect


def test_goto_and_title(mp_page, html_url):
    mp_page.goto(html_url)
    assert mp_page.title() == "miniplaywright fixture"
    expect(mp_page).to_have_url("page.html")


def test_click(mp_page, html_url):
    mp_page.goto(html_url)
    mp_page.locator("#btn").click()
    expect(mp_page.locator("#out")).to_have_text("clicked")


def test_fill_dispatches_input(mp_page, html_url):
    mp_page.goto(html_url)
    mp_page.locator("#name").fill("alice")
    expect(mp_page.locator("#echo")).to_have_text("alice")


def test_expect_visible_and_count(mp_page, html_url):
    mp_page.goto(html_url)
    expect(mp_page.locator("#title")).to_be_visible()
    expect(mp_page.locator("li")).to_have_count(2)
    expect(mp_page.locator("#title")).to_contain_text("Hell")


def test_auto_wait_for_delayed_text(mp_page, html_url):
    mp_page.goto(html_url)
    expect(mp_page.locator("#delayed")).to_have_text("ready", timeout=3)


def test_screenshot(mp_page, html_url, tmp_path):
    mp_page.goto(html_url)
    target = mp_page.screenshot(tmp_path / "shot.png")
    assert target.exists()
    assert target.stat().st_size > 1000
