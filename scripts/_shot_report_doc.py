from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(r"E:\ailearning\ai-qa-lab\docs\shots")
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto("https://ai-qa-lab-production.up.railway.app/ui/#/skill-docs", wait_until="networkidle")
    page.wait_for_timeout(1200)
    page.get_by_text("shenle-report-generate-html", exact=True).first.click()
    page.wait_for_timeout(1200)
    has_zip = page.get_by_text("下载 zip").count()
    page.screenshot(path=str(OUT / "prod-skill-docs-report.png"))
    print("下载按钮数", has_zip)
    browser.close()
