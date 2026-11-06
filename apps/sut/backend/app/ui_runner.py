"""Execute UI steps with Playwright and record what happened.

The runner is deliberately small: it launches headless Chromium, optionally
seeds localStorage (the "免登录" trick), then walks the steps and stops at the
first failure. A screenshot is kept when something breaks.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from . import ui_models as models
from .ui_steps import normalise_steps, parse_env

ROOT = Path(__file__).resolve().parents[4]
SHOT_DIR = ROOT / "data" / "ui-shots"
BROWSERS = ROOT / ".pw-browsers"
DEFAULT_TIMEOUT = 10000

# Playwright reads this env var when it resolves the browser binary. The repo
# keeps Chromium on E: so nothing has to live on the system drive.
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(BROWSERS))


class RunError(RuntimeError):
    """Raised when the browser cannot even start."""


def _playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on env
        raise RunError(
            "后端没有安装 playwright，执行 UI 用例前请先运行："
            ".venv\\Scripts\\python.exe -m pip install playwright && "
            ".venv\\Scripts\\python.exe -m playwright install chromium"
        ) from exc
    return sync_playwright


def _locator(page, target: str):
    # A selector like ``text=知识库`` often matches the sidebar entry and the
    # page title at once. Taking the first match keeps generated cases usable
    # instead of failing on Playwright's strict-mode check.
    return page.locator(target).first


def _run_step(page, step: dict[str, Any]) -> None:
    action = step["action"]
    timeout = int(step.get("timeout") or DEFAULT_TIMEOUT)
    if action == "goto":
        page.goto(step["value"], wait_until="domcontentloaded", timeout=max(timeout, 15000))
    elif action == "click":
        _locator(page, step["target"]).click(timeout=timeout)
    elif action == "fill":
        _locator(page, step["target"]).fill(step["value"], timeout=timeout)
    elif action == "press":
        _locator(page, step["target"]).press(step["value"], timeout=timeout)
    elif action == "select":
        _locator(page, step["target"]).select_option(step["value"], timeout=timeout)
    elif action == "hover":
        _locator(page, step["target"]).hover(timeout=timeout)
    elif action == "wait":
        page.wait_for_timeout(int(step.get("ms") or 800))
    elif action == "assert_text":
        text = _locator(page, step["target"]).inner_text(timeout=timeout)
        if step["value"] not in text:
            raise AssertionError(f"页面文字里没有「{step['value']}」")
    elif action == "assert_visible":
        if not _locator(page, step["target"]).is_visible(timeout=timeout):
            raise AssertionError(f"元素不可见：{step['target']}")
    elif action == "assert_url":
        if step["value"] not in page.url:
            raise AssertionError(f"地址里没有「{step['value']}」，当前是 {page.url}")
    elif action == "screenshot":
        page.screenshot(full_page=True)
    else:  # pragma: no cover - guarded by normalise_steps
        raise AssertionError(f"未实现的动作 {action}")


def execute_case(case: models.UiCase, *, run_id: int | None = None, headless: bool = True) -> dict:
    """Run one case; returns the payload stored on the run row."""
    steps = normalise_steps(case.steps_json)
    env = parse_env(case.env_json)

    results: list[dict[str, Any]] = []
    error_text: str | None = None
    shot_path: str | None = None

    sync_playwright = _playwright()
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=headless)
        except Exception as exc:  # noqa: BLE001 - surface a readable message
            raise RunError(f"浏览器启动失败：{exc}") from exc
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        if env:
            payload = json.dumps(env, ensure_ascii=False)
            context.add_init_script(
                "(() => { const data = %s;"
                " for (const [k, v] of Object.entries(data)) localStorage.setItem(k, v); })();"
                % payload
            )
        page = context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)

        started = page.evaluate("() => Date.now()")
        for index, step in enumerate(steps):
            record: dict[str, Any] = {
                "index": index,
                "name": step.get("name") or step["action"],
                "action": step["action"],
                "target": step.get("target"),
                "value": step.get("value"),
                "ok": True,
                "error": None,
            }
            try:
                _run_step(page, step)
            except Exception as exc:  # noqa: BLE001 - step failures are data
                record["ok"] = False
                record["error"] = str(exc).split("\n")[0][:400]
                error_text = f"第 {index + 1} 步失败：{record['error']}"
                results.append(record)
                break
            results.append(record)

        if error_text:
            SHOT_DIR.mkdir(parents=True, exist_ok=True)
            name = f"ui-run-{run_id or 'adhoc'}.png"
            try:
                page.screenshot(path=str(SHOT_DIR / name), full_page=True)
                shot_path = name
            except Exception:  # noqa: BLE001 - screenshot is best effort
                shot_path = None
        try:
            finished = page.evaluate("() => Date.now()")
        except Exception:  # noqa: BLE001
            finished = started
        browser.close()

    return {
        "steps": results,
        "error": error_text,
        "screenshot": shot_path,
        "duration_ms": int(max(0, finished - started)),
    }


def snapshot(url: str, *, env: dict[str, str] | None = None, headless: bool = True) -> dict:
    """Open a page and return a compact description the model can reason about."""
    sync_playwright = _playwright()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        if env:
            context.add_init_script(
                "(() => { const data = %s;"
                " for (const [k, v] of Object.entries(data)) localStorage.setItem(k, v); })();"
                % json.dumps(env, ensure_ascii=False)
            )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(800)
        data = page.evaluate(
            """() => {
              const pick = (el) => ({
                tag: el.tagName.toLowerCase(),
                text: (el.innerText || el.value || el.placeholder || '').trim().slice(0, 60),
                name: el.getAttribute('name') || '',
                id: el.id || '',
                placeholder: el.getAttribute('placeholder') || '',
                type: el.getAttribute('type') || '',
                role: el.getAttribute('role') || '',
                href: (el.getAttribute('href') || '').slice(0, 120),
              });
              const nodes = Array.from(
                document.querySelectorAll('a, button, input, select, textarea, [role=button]')
              ).slice(0, 80).map(pick);
              return {
                title: document.title,
                url: location.href,
                text: (document.body.innerText || '').slice(0, 3000),
                nodes,
              };
            }"""
        )
        browser.close()
    return data
