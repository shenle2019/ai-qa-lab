from pathlib import Path

import pytest

from libs.miniplaywright import launch


@pytest.fixture(scope="session")
def browser():
    try:
        instance = launch()
    except Exception as exc:
        pytest.skip(f"browser unavailable: {exc}")
    yield instance
    instance.close()


@pytest.fixture
def page(browser):
    return browser.page


@pytest.fixture
def html_url(tmp_path: Path) -> str:
    target = tmp_path / "page.html"
    target.write_text(
        """
<!doctype html>
<html>
<head><title>miniplaywright fixture</title></head>
<body>
  <h1 id="title">Hello</h1>
  <button id="btn" onclick="document.getElementById('out').innerText='clicked'">Click</button>
  <input id="name" oninput="document.getElementById('echo').innerText=this.value" />
  <p id="out"></p>
  <p id="echo"></p>
  <ul><li>a</li><li>b</li></ul>
  <div id="delayed"></div>
  <script>
    setTimeout(() => { document.getElementById('delayed').innerText = 'ready'; }, 300);
  </script>
</body>
</html>
""".strip(),
        encoding="utf-8",
    )
    return target.as_uri()
