import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

B = "https://ai-qa-lab-production.up.railway.app"
KEY = os.environ.get("APP_API_KEY", "")
OUT = Path(r"E:\ailearning\ai-qa-lab\docs\shots")
OUT.mkdir(parents=True, exist_ok=True)


def get(path: str) -> tuple[int, str]:
    req = urllib.request.Request(B + path, headers={"X-API-Key": KEY} if KEY else {})
    try:
        with urllib.request.urlopen(req, timeout=40) as res:
            return res.status, res.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "ignore")


print("404:", get("/api/platform/skill-docs/nope")[0], get("/api/platform/skill-docs/nope")[1][:60])
print("bad slug:", get("/api/platform/skill-docs/..%2Fetc/download")[0])

items = json.loads(get("/api/platform/skill-docs")[1])
print("count", len(items), "| missing zip:", [i["slug"] for i in items if not i["has_zip"]])

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(B + "/ui/#/skill-docs", wait_until="networkidle")
    page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT / "prod-skill-docs-synced.png"))
    rows = page.locator(".doc-list button, .doc-item").count()
    print("ui rows", rows, "| title", page.title())
    browser.close()
