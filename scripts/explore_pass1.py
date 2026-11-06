"""Exploratory pass 1: walk every route, record what a first-time user sees.

Read-only: only navigation, no form submits that write data.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "explore" / "2026-11-06-exploratory" / "pass1.json"
SHOTS = ROOT / "docs" / "explore" / "2026-11-06-exploratory" / "shots"
UI = "http://127.0.0.1:8000/ui/#"

ROUTES = [
    ("/", "landing"),
    ("/projects", "projects"),
    ("/project-overview", "overview"),
    ("/requirements", "requirements"),
    ("/functional", "functional"),
    ("/kb", "kb"),
    ("/environments", "environments"),
    ("/api-automation", "api"),
    ("/ui-automation", "ui"),
    ("/modules", "modules"),
    ("/members", "members"),
    ("/system-ai", "system-ai"),
    ("/ai-logs", "ai-logs"),
    ("/users", "users"),
    ("/dashboard", "legacy-dashboard"),
    ("/tickets", "legacy-tickets"),
    ("/nope-does-not-exist", "unknown-route"),
]


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        console: list[str] = []
        failed: list[str] = []
        page.on("console", lambda msg: console.append(f"{msg.type}: {msg.text}") if msg.type in ("error", "warning") else None)
        page.on("requestfailed", lambda req: failed.append(f"{req.method} {req.url} {req.failure}"))

        for route, key in ROUTES:
            console.clear()
            failed.clear()
            started = time.time()
            page.goto(UI + route, wait_until="networkidle")
            page.wait_for_timeout(900)
            info = page.evaluate(
                """() => {
                const txt = (el) => (el ? el.innerText.trim().slice(0, 200) : '');
                const buttons = [...document.querySelectorAll('button')].map(b => b.innerText.trim()).filter(Boolean);
                const links = [...document.querySelectorAll('a')].map(a => a.getAttribute('href')).filter(Boolean);
                const inputs = [...document.querySelectorAll('input,select,textarea')].map(i => i.getAttribute('placeholder') || i.tagName.toLowerCase());
                const active = document.querySelector('.nav-item.router-link-exact-active');
                return {
                  hash: location.hash,
                  pageTitle: txt(document.querySelector('.page-head h1') || document.querySelector('h1')),
                  heroTitle: txt(document.querySelector('.hero h2')),
                  heroSub: txt(document.querySelector('.hero .muted')),
                  buttons: buttons.slice(0, 12),
                  buttonCount: buttons.length,
                  inputs: inputs.slice(0, 12),
                  empty: txt(document.querySelector('.empty')),
                  placeholder: txt(document.querySelector('.module-planned')),
                  activeNav: txt(active),
                  bodyLen: document.body.innerText.length,
                  scrollH: document.documentElement.scrollHeight,
                };
            }"""
            )
            info["route"] = route
            info["key"] = key
            info["console"] = console[:6]
            info["requestFailed"] = failed[:4]
            info["elapsed_ms"] = int((time.time() - started) * 1000)
            results.append(info)
            page.screenshot(path=str(SHOTS / f"{key}.png"))
            print(f"{key:18} {info['hash']:22} btn={info['buttonCount']:2} empty={info['empty'][:28]!r}")

        browser.close()

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
