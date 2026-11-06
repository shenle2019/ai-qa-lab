"""Exploratory pass 2: targeted probes on the paths a first-time user takes.

Strictly read-only: navigation, opening modals, typing. No writes; the two
empty-submit probes are guarded by client-side validation (verified in source).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs" / "explore" / "2026-11-06-exploratory"
SHOTS = DIR / "shots"
UI = "http://127.0.0.1:8000/ui/#"

LEGACY = [
    ("/workbench", "legacy-workbench"),
    ("/knowledge", "legacy-knowledge"),
    ("/platform", "legacy-platform"),
    ("/models", "legacy-models"),
    ("/testcases", "legacy-testcases"),
    ("/methodology", "legacy-methodology"),
    ("/report", "legacy-report"),
    ("/portfolio", "legacy-portfolio"),
    ("/login", "legacy-login"),
]


def main() -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    notes: list[dict] = []

    def add(probe: str, observation: str, **extra) -> None:
        notes.append({"probe": probe, "observation": observation, **extra})
        print(f"[{probe}] {observation[:150]}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        console: list[str] = []
        page.on("console", lambda m: console.append(f"{m.type}: {m.text}") if m.type == "error" else None)

        # A. overview with no project chosen
        page.goto(UI + "/overview", wait_until="networkidle")
        page.wait_for_timeout(800)
        body = page.inner_text("body")
        add("overview-noproject", "hero 文案 = " + page.inner_text(".hero")[:160].replace("\n", " / "))
        add("overview-noproject", "是否有「先去建项目」引导: " + str("项目" in body and "新建" in body))
        page.screenshot(path=str(SHOTS / "overview-noproject.png"))

        # B. legacy pages still reachable
        for route, key in LEGACY:
            console.clear()
            page.goto(UI + route, wait_until="networkidle")
            page.wait_for_timeout(700)
            title = page.evaluate("() => (document.querySelector('.page-head h1')||document.querySelector('h1')||{}).innerText || ''")
            errs = len(console)
            add("legacy", f"{route} -> {title.strip()[:24]!r} console_err={errs}")
            page.screenshot(path=str(SHOTS / f"{key}.png"))

        # C. empty project name
        page.goto(UI + "/projects", wait_until="networkidle")
        page.wait_for_timeout(600)
        page.locator("button", has_text="创建项目").first.click()
        page.wait_for_timeout(500)
        alert = page.locator(".alert").first
        add("projects-empty-name", "点击创建（名称空）→ " + (alert.inner_text() if alert.count() else "无提示"), shot="projects-empty-name.png")
        page.screenshot(path=str(SHOTS / "projects-empty-name.png"))

        # D. empty user name
        page.goto(UI + "/users", wait_until="networkidle")
        page.wait_for_timeout(700)
        page.locator("button", has_text="添加").first.click()
        page.wait_for_timeout(500)
        alert = page.locator(".alert").first
        add("users-empty-name", "点击添加（用户名空）→ " + (alert.inner_text() if alert.count() else "无提示"))
        page.screenshot(path=str(SHOTS / "users-empty-name.png"))

        # E. project selection persistence across reload and navigation
        page.goto(UI + "/api-automation", wait_until="networkidle")
        page.wait_for_timeout(1200)
        select = page.locator("select").first
        options = select.locator("option").all_inner_texts()
        current = select.input_value()
        add("api-project-default", f"默认项目 = {select.locator('option').nth(0).inner_text()!r}（共 {len(options)} 个）")
        if len(options) > 2:
            select.select_option(index=2)
            page.wait_for_timeout(900)
            picked = select.input_value()
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(1000)
            after = page.locator("select").first.input_value()
            add("api-project-persist", f"选第3个项目 value={picked} → 刷新后 value={after}，一致={picked == after}")

        # F. table overflow on narrow viewport
        for width in (1024, 480):
            page.set_viewport_size({"width": width, "height": 800})
            page.goto(UI + "/functional", wait_until="networkidle")
            page.wait_for_timeout(800)
            overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            add("functional-narrow", f"{width}px 宽：横向溢出 {overflow}px")
            if width == 480:
                page.screenshot(path=str(SHOTS / "functional-480.png"))
        page.set_viewport_size({"width": 1440, "height": 900})

        # G. kb chunk modal (read-only)
        page.goto(UI + "/kb", wait_until="networkidle")
        page.wait_for_timeout(1000)
        chunk = page.locator("table button", has_text="分块")
        if chunk.count():
            chunk.first.click()
            page.wait_for_timeout(700)
            has_modal = page.locator(".modal-mask").count()
            add("kb-chunk-modal", f"点「分块」→ 弹窗层数 {has_modal}")
            page.screenshot(path=str(SHOTS / "kb-chunk-modal.png"))
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            add("kb-chunk-modal", f"按 Esc 后弹窗数 {page.locator('.modal-mask').count()}（0 表示可关）")

        # H. api debug drawer, without sending
        page.goto(UI + "/api-automation", wait_until="networkidle")
        page.wait_for_timeout(1000)
        debug = page.locator("table button", has_text="调试")
        if debug.count():
            debug.first.click()
            page.wait_for_timeout(800)
            drawer_text = page.inner_text(".modal-mask")[:200].replace("\n", " / ")
            add("api-debug-drawer", "调试抽屉内容: " + drawer_text)
            page.screenshot(path=str(SHOTS / "api-debug-drawer.png"))
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)

        # I. unknown route escape hatch
        page.goto(UI + "/nope", wait_until="networkidle")
        page.wait_for_timeout(600)
        links = page.evaluate("() => [...document.querySelectorAll('a')].map(a => a.innerText.trim()).filter(Boolean).slice(0,8)")
        add("unknown-route", "404 页可点链接: " + str(links))
        page.screenshot(path=str(SHOTS / "unknown-route.png"))

        # J. keyboard focus
        page.goto(UI + "/projects", wait_until="networkidle")
        page.wait_for_timeout(600)
        seq = []
        for _ in range(6):
            page.keyboard.press("Tab")
            info = page.evaluate(
                """() => {
                const el = document.activeElement;
                const cs = getComputedStyle(el);
                return [el.tagName, (el.innerText||el.placeholder||'').trim().slice(0,12), cs.outlineStyle, cs.outlineWidth, cs.boxShadow.slice(0,30)];
            }"""
            )
            seq.append(info)
        add("keyboard-tab", "Tab 序列: " + json.dumps(seq, ensure_ascii=False))

        # K. long text in search box
        page.goto(UI + "/functional", wait_until="networkidle")
        page.wait_for_timeout(800)
        search = page.locator("input[type='search']").first
        if search.count():
            search.fill("很长的搜索词" * 40)
            page.wait_for_timeout(300)
            overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            add("long-search-text", f"200 字搜索词：横向溢出 {overflow}px")

        browser.close()

    (DIR / "pass2.json").write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", DIR / "pass2.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
