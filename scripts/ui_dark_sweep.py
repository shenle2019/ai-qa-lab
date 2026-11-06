"""Sweep every route and look for panels that stayed dark after the light theme."""

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000/ui/"
OUT = Path("docs/ui-v4")

PAGES = [
    ("overview", "#/overview"),
    ("projects", "#/projects"),
    ("requirements", "#/requirements"),
    ("functional", "#/functional"),
    ("kb", "#/kb"),
    ("environments", "#/environments"),
    ("api", "#/api-automation"),
    ("ui", "#/ui-automation"),
    ("modules", "#/modules"),
    ("members", "#/members"),
    ("users", "#/users"),
    ("system-ai", "#/system-ai"),
    ("ai-logs", "#/ai-logs"),
    ("tools", "#/tools"),
]

DARK = """
() => {
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    const rect = el.getBoundingClientRect();
    if (rect.width * rect.height < 4000) continue;
    const bg = getComputedStyle(el).backgroundColor;
    const m = bg.match(/rgba?\\((\\d+), (\\d+), (\\d+)(?:, ([\\d.]+))?\\)/);
    if (!m) continue;
    const [r, g, b] = [Number(m[1]), Number(m[2]), Number(m[3])];
    const alpha = m[4] === undefined ? 1 : Number(m[4]);
    if (alpha < 0.5) continue;
    const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    if (lum > 60) continue;
    out.push(el.tagName.toLowerCase() + '.' + (el.className || '').toString().split(' ')[0]
      + ' ' + Math.round(rect.width) + 'x' + Math.round(rect.height) + ' ' + bg);
  }
  return out.slice(0, 6);
}
"""


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        for name, path in PAGES:
            page.goto(BASE + path, wait_until="load")
            page.wait_for_timeout(1400)
            dark = page.evaluate(DARK)
            page.screenshot(path=str(OUT / f"v4-{name}.png"), full_page=True)
            print(name, "dark:", dark if dark else "none")
        print("pageerrors", len(errors))
        browser.close()


if __name__ == "__main__":
    main()
