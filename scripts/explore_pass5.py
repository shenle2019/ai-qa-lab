"""Re-check the 16 exploratory findings after the fix round."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "explore" / "2026-11-06-exploratory" / "shots"
UI = "http://127.0.0.1:8000/ui/#"

results: list[dict] = []


def check(key: str, ok: bool, detail: str) -> None:
    results.append({"id": key, "ok": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + key + " :: " + detail)


def main() -> int:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errors: list[str] = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        # 1. requirement modal shows the validation error inside the dialog
        page.goto(UI + "/requirements", wait_until="networkidle")
        page.wait_for_timeout(900)
        page.locator("button", has_text="新建需求").first.click()
        page.wait_for_timeout(600)
        page.locator(".modal button", has_text="确定").first.click()
        page.wait_for_timeout(500)
        inside = page.locator(".modal-mask .alert.error").count()
        page.screenshot(path=str(SHOTS / "after-req-modal-error.png"))
        check("1 modal-error-visible", inside >= 1, f"alert inside modal = {inside}")

        # 6. Escape closes the dialog
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        still_open = page.locator(".modal-mask").count()
        check("6 esc-closes-modal", still_open == 0, f"modal after Esc = {still_open}")

        # 2. overview wording
        page.goto(UI + "/overview", wait_until="networkidle")
        page.wait_for_timeout(900)
        text = page.locator(".content").inner_text()
        page.screenshot(path=str(SHOTS / "after-overview.png"))
        check("2a overview-no-dash", "项目 #—" not in text, "hero label")
        check(
            "2b overview-passrate-label",
            "按用例结果统计" in text and "全平台累计执行次数" in text,
            "pass-rate + executions hints",
        )

        # 3. legacy group labelled
        summary_text = page.locator(".nav-more summary").first.inner_text()
        legacy_count = page.locator(".nav-more .nav-item.nav-legacy").count()
        page.locator(".nav-more summary").first.click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(SHOTS / "after-devtools.png"))
        check(
            "3 legacy-labelled",
            "旧版" in summary_text and legacy_count == 10,
            f"summary={summary_text.strip()} legacy links={legacy_count}",
        )

        # 16. icons unique outside the legacy group
        icons = page.locator(".nav-group:not(.nav-more) .nav-icon").all_inner_texts()
        check("16 icons-unique", len(set(icons)) == len(icons), f"{len(icons)} icons")

        # 8. health button gives feedback
        page.locator(".topbar button", has_text="检测服务").click()
        page.wait_for_timeout(900)
        notice = page.locator(".topbar .muted").first.inner_text()
        check("8 health-feedback", "服务" in notice, f"notice={notice.strip()}")

        # 15. docs link present while docs enabled
        docs = page.locator(".topbar a", has_text="API 文档").count()
        check("15 docs-link", docs == 1, f"docs links = {docs}")

        # 4. 404 goes back to the new overview
        page.goto(UI + "/project-overview", wait_until="networkidle")
        page.wait_for_timeout(700)
        btn = page.locator("button, a", has_text="返回项目概览").first
        label = btn.inner_text().strip()
        btn.click()
        page.wait_for_timeout(700)
        check(
            "4 404-target",
            "项目概览" in label and page.url.endswith("/overview"),
            f"button={label} url={page.url.split('#')[-1]}",
        )

        # 5. environments page is real
        page.goto(UI + "/environments", wait_until="networkidle")
        page.wait_for_timeout(1100)
        env_text = page.locator(".content").inner_text()
        page.screenshot(path=str(SHOTS / "after-environments.png"))
        check(
            "5 environments-real",
            "规划中" not in env_text and "environment.list" not in env_text and "保存环境" in env_text,
            "no placeholder text, form present",
        )

        # 10. modules follows the shared project key
        page.evaluate("window.localStorage.setItem('aiqa.project','2')")
        page.goto(UI + "/modules", wait_until="networkidle")
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(1400)
        selected = page.locator(".toolbar select").first.evaluate("el => el.value")
        check("10 shared-project", str(selected) == "2", f"selected project={selected}")

        page.evaluate("window.localStorage.removeItem('aiqa.project')")
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(1500)
        default_project = page.locator(".toolbar select").first.evaluate("el => el.value")
        check(
            "10b busy-default",
            str(default_project) == "2",
            f"default project without memory={default_project}",
        )

        # 9. single agent generate disabled without an endpoint
        page.goto(UI + "/api-automation", wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.locator(".tab, .tabs .tab", has_text="单接口 Agent").first.click()
        page.wait_for_timeout(700)
        disabled = page.locator("button", has_text="AI 生成用例").first.is_disabled()
        # 11. debug drawer placeholder
        page.locator(".tabs .tab", has_text="接口管理").first.click()
        page.wait_for_timeout(700)
        page.locator("table button", has_text="调试").first.click()
        page.wait_for_timeout(900)
        placeholder = page.locator(".modal-mask input.mono").first.get_attribute("placeholder")
        page.screenshot(path=str(SHOTS / "after-debug-drawer.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        check("9 single-agent-disabled", disabled, "generate disabled with no endpoint")
        check("11 debug-baseurl-hint", "留空则用接口资产地址" in (placeholder or ""), str(placeholder))

        # 12. search inputs are length-capped
        page.goto(UI + "/functional", wait_until="networkidle")
        page.wait_for_timeout(900)
        maxlen = page.locator("input[type='search']").first.get_attribute("maxlength")
        check("12 search-maxlength", maxlen == "80", f"maxlength={maxlen}")

        # 7. focus ring is visible (accent colour, not near-black)
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        page.wait_for_timeout(300)
        outline = page.evaluate(
            """() => {
                const el = document.activeElement
                const style = getComputedStyle(el)
                return { tag: el.tagName, color: style.outlineColor, width: style.outlineWidth,
                         shadow: style.boxShadow }
            }"""
        )
        page.screenshot(path=str(SHOTS / "after-focus.png"))
        accent = "56, 189, 248"
        check(
            "7 focus-ring",
            accent in outline["color"] or accent in outline["shadow"],
            json.dumps(outline, ensure_ascii=False),
        )

        # 13. narrow screen: sidebar becomes a drawer with a toggle
        narrow = browser.new_page(viewport={"width": 480, "height": 800})
        narrow.goto(UI + "/functional", wait_until="networkidle")
        narrow.wait_for_timeout(900)
        toggle_visible = narrow.locator(".menu-toggle").is_visible()
        offscreen = narrow.locator(".sidebar").evaluate("el => el.getBoundingClientRect().right <= 1")
        narrow.screenshot(path=str(SHOTS / "after-narrow-closed.png"))
        narrow.locator(".menu-toggle").click()
        narrow.wait_for_timeout(500)
        opened = narrow.locator(".sidebar").evaluate("el => el.getBoundingClientRect().left >= 0")
        narrow.screenshot(path=str(SHOTS / "after-narrow-open.png"))
        check(
            "13 narrow-drawer",
            toggle_visible and offscreen and opened,
            f"toggle={toggle_visible} hidden={offscreen} opened={opened}",
        )
        narrow.close()

        # 14. file input and selects share the dark theme
        page.goto(UI + "/requirements", wait_until="networkidle")
        page.wait_for_timeout(800)
        page.locator("button", has_text="新建需求").first.click()
        page.wait_for_timeout(600)
        picker = page.locator(".modal input[type='file']").first.evaluate(
            "el => getComputedStyle(el).color"
        )
        check(
            "14 file-input-themed",
            picker != "rgb(230, 237, 247)",
            f"color={picker} (must not be the bright text colour)",
        )
        page.keyboard.press("Escape")

        check("no-console-errors", not errors, f"{len(errors)} console errors")

        browser.close()

    payload = {"results": results, "passed": sum(1 for item in results if item["ok"]), "total": len(results)}
    out_dir = ROOT / "docs" / "explore" / "2026-11-06-exploratory"
    (out_dir / "pass5.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{payload['passed']}/{payload['total']} checks passed")
    return 0 if payload["passed"] == payload["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
