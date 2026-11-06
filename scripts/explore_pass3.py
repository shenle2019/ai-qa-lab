"""Exploratory pass 3: modal behaviour, keyboard, and long-input probes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs" / "explore" / "2026-11-06-exploratory"
SHOTS = DIR / "shots"
UI = "http://127.0.0.1:8000/ui/#"


def main() -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    notes: list[dict] = []

    def add(probe: str, observation: str) -> None:
        notes.append({"probe": probe, "observation": observation})
        print(f"[{probe}] {observation.encode('ascii', 'replace').decode()[:160]}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        # 1. unknown route escape hatch
        page.goto(UI + "/nope", wait_until="networkidle")
        page.wait_for_timeout(600)
        links = page.evaluate("() => [...document.querySelectorAll('a')].map(a => a.innerText.trim()).filter(Boolean).slice(0,10)")
        add("unknown-route", f"links={links}")

        # 2. keyboard tab order
        page.goto(UI + "/projects", wait_until="networkidle")
        page.wait_for_timeout(600)
        seq = []
        for _ in range(8):
            page.keyboard.press("Tab")
            seq.append(
                page.evaluate(
                    """() => {
                    const el = document.activeElement;
                    const cs = getComputedStyle(el);
                    return {tag: el.tagName, label: (el.innerText||el.placeholder||el.value||'').trim().slice(0,10),
                            outline: cs.outlineStyle + '/' + cs.outlineWidth, shadow: cs.boxShadow.slice(0,24)};
                }"""
                )
            )
        add("keyboard-tab", json.dumps(seq, ensure_ascii=False))

        # 3. long text in search
        page.goto(UI + "/functional", wait_until="networkidle")
        page.wait_for_timeout(700)
        search = page.locator("input[type='search']").first
        if search.count():
            search.fill("很长的搜索词" * 40)
            page.wait_for_timeout(300)
            overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            add("long-search-text", f"overflow={overflow}px rows={page.locator('table tbody tr').count()}")

        # 4. modal close: Esc and mask click
        page.goto(UI + "/kb", wait_until="networkidle")
        page.wait_for_timeout(900)
        chunk = page.locator("table button", has_text="分块")
        if chunk.count():
            chunk.first.click()
            page.wait_for_timeout(600)
            add("kb-modal-open", f"mask={page.locator('.modal-mask').count()}")
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            add("kb-modal-esc", f"after Esc mask={page.locator('.modal-mask').count()}")
            page.mouse.click(30, 450)
            page.wait_for_timeout(400)
            add("kb-modal-maskclick", f"after mask click mask={page.locator('.modal-mask').count()}")
            page.screenshot(path=str(SHOTS / "kb-modal-after-maskclick.png"))
            if page.locator(".modal-mask").count():
                page.locator("button", has_text="关闭").first.click()
                page.wait_for_timeout(300)

        # 5. requirement modal: empty submit -> is the error visible?
        page.goto(UI + "/requirements", wait_until="networkidle")
        page.wait_for_timeout(900)
        new_btn = page.locator("button", has_text="新建需求")
        if new_btn.count():
            new_btn.first.click()
            page.wait_for_timeout(600)
            add("req-modal-title", page.inner_text(".modal-mask header")[:60] if page.locator(".modal-mask header").count() else "no header")
            confirm = page.locator(".modal-mask button", has_text="确定")
            if confirm.count():
                confirm.first.click()
                page.wait_for_timeout(600)
                inside = page.locator(".modal-mask .alert").count()
                outside = page.locator(".alert").count()
                add("req-empty-submit", f"modal still open={page.locator('.modal-mask').count()} alerts_inside_modal={inside} alerts_total={outside}")
                page.screenshot(path=str(SHOTS / "req-empty-submit.png"))
                page.keyboard.press("Escape")
                close = page.locator(".modal-mask button", has_text="取消")
                if close.count():
                    close.first.click()
                page.wait_for_timeout(300)

        # 6. API 文档 button + dev-tools group
        page.goto(UI + "/projects", wait_until="networkidle")
        page.wait_for_timeout(600)
        doc_link = page.locator("a", has_text="API 文档").first
        add("api-doc-link", f"href={doc_link.get_attribute('href') if doc_link.count() else 'none'} target={doc_link.get_attribute('target') if doc_link.count() else '-'}")
        dev = page.locator("details").first
        if dev.count():
            dev.locator("summary").click()
            page.wait_for_timeout(400)
            items = page.locator("details a").count()
            add("devtools-group", f"开发工具组内链接数={items}")
            page.screenshot(path=str(SHOTS / "devtools-open.png"))

        # 7. single-endpoint agent tab, is the button enabled with no endpoint?
        page.goto(UI + "/api-automation", wait_until="networkidle")
        page.wait_for_timeout(900)
        page.locator(".tabs .tab", has_text="单接口 Agent").first.click()
        page.wait_for_timeout(600)
        btns = page.evaluate("() => [...document.querySelectorAll('button')].filter(b => b.innerText.includes('生成')).map(b => [b.innerText.trim(), b.disabled])")
        add("single-agent", f"generate buttons={btns}")
        page.screenshot(path=str(SHOTS / "api-single-agent.png"))

        browser.close()

    (DIR / "pass3.json").write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
