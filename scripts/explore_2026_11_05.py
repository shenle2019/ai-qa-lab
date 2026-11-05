"""One-off exploratory testing harness (2026-11-05).

Drives the deployed SUT UI with libs.miniplaywright, records one JSON line per
step to docs/explore/2026-11-05/log.jsonl, and saves a screenshot.

Read-only by design: it only navigates, clicks, and types. It never calls the
write API directly and never submits a create/update/delete form on purpose.

Usage:
  python scripts/explore_2026_11_05.py --name 001-home --url "...#/"
  python scripts/explore_2026_11_05.py --name 002-click --url "...#/" \\
      --click "body > div:nth-of-type(1) > a:nth-of-type(2)"
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "explore" / "2026-11-05"
SHOTS = OUT / "screenshots"
LOG = OUT / "log.jsonl"

INIT_SCRIPT = r"""
(() => {
  const probe = window.__probe = { errors: [], net: [], nav: [] };
  const push = (kind, msg) => probe.errors.push({ kind, msg: String(msg).slice(0, 500) });
  const origError = console.error.bind(console);
  console.error = (...args) => { push('console.error', args.map(a => {
    try { return typeof a === 'object' ? JSON.stringify(a) : String(a); } catch (e) { return String(a); }
  }).join(' ')); origError(...args); };
  const origWarn = console.warn.bind(console);
  console.warn = (...args) => { push('console.warn', args.map(String).join(' ')); origWarn(...args); };
  window.addEventListener('error', e => push('window.error', e.message + ' @ ' + (e.filename || '') + ':' + (e.lineno || '')));
  window.addEventListener('unhandledrejection', e => push('unhandledrejection', e.reason && (e.reason.stack || e.reason.message) || e.reason));
  const origFetch = window.fetch;
  if (origFetch) {
    window.fetch = async (...args) => {
      const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
      const method = (args[1] && args[1].method) || 'GET';
      try {
        const res = await origFetch.apply(window, args);
        if (res.status >= 400) probe.net.push({ method, url: String(url).slice(0, 300), status: res.status });
        return res;
      } catch (err) { probe.net.push({ method, url: String(url).slice(0, 300), status: 'network-error' }); throw err; }
    };
  }
  const origOpen = XMLHttpRequest.prototype.open;
  const origSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (method, url, ...rest) {
    this.__probe = { method, url: String(url) }; return origOpen.call(this, method, url, ...rest);
  };
  XMLHttpRequest.prototype.send = function (...args) {
    this.addEventListener('loadend', () => {
      if (this.status >= 400) probe.net.push({ method: this.__probe?.method, url: String(this.__probe?.url || '').slice(0, 300), status: this.status });
    });
    return origSend.apply(this, args);
  };
})();
"""

SNAPSHOT_JS = r"""
(() => {
  const isVisible = el => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && r.bottom > -50 && r.top < (window.innerHeight + 200);
  };
  const clean = v => String(v || '').replace(/\s+/g, ' ').trim().slice(0, 120);
  const label = el => clean(el.innerText || el.value || el.getAttribute('placeholder') || el.getAttribute('aria-label') || el.getAttribute('title') || '');
  const path = el => {
    if (el.id) return '#' + CSS.escape(el.id);
    const parts = [];
    let c = el;
    while (c && c.nodeType === 1 && c !== document.body) {
      let i = 1, s = c;
      while ((s = s.previousElementSibling)) if (s.tagName === c.tagName) i++;
      parts.unshift(c.tagName.toLowerCase() + ':nth-of-type(' + i + ')');
      c = c.parentElement;
    }
    return 'body > ' + parts.join(' > ');
  };
  const nodes = [...document.querySelectorAll('a,button,input,select,textarea,[role="button"],[onclick]')].filter(isVisible);
  const items = nodes.slice(0, 120).map(el => ({
    tag: el.tagName.toLowerCase(), type: el.getAttribute('type') || '', text: label(el),
    href: el.getAttribute('href') || '', disabled: !!el.disabled, value: el.tagName === 'INPUT' ? clean(el.value).slice(0, 40) : '',
    sel: path(el)
  }));
  const links = [...document.querySelectorAll('a[href]')].map(a => ({ text: clean(a.innerText), href: a.getAttribute('href') }));
  return {
    title: document.title,
    url: location.href,
    scrollHeight: document.documentElement.scrollHeight,
    bodyText: (document.body ? document.body.innerText : '').slice(0, 6000),
    items,
    links,
    probe: window.__probe || { errors: [], net: [] },
    localKeys: Object.keys(localStorage),
    sessionKeys: Object.keys(sessionStorage)
  };
})()
"""


def judge(before: dict | None, after: dict, action: str) -> tuple[str, str]:
    """Heuristic first-pass judgment; I override it manually on review."""
    text = (after.get("bodyText") or "").lower()
    errors = [e for e in (after.get("probe", {}).get("errors") or [])]
    bad_net = [n for n in (after.get("probe", {}).get("net") or [])]
    if any(k in text for k in ("internal server error", "traceback", "undefined is not", "cannot read propert")):
        return "疑似异常", "正文出现报错/异常堆栈"
    if bad_net:
        return "疑似异常", f"网络请求 {len(bad_net)} 个 4xx/5xx"
    if errors:
        return "疑似", f"控制台有 {len(errors)} 条 error/warn"
    if before and before.get("url") == after.get("url") and action.startswith(("click", "fill")) and after.get("scrollHeight") == before.get("scrollHeight"):
        return "疑似", "操作后 URL 与页面高度均未变化"
    return "正常", ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--wait", type=float, default=2.5)
    ap.add_argument("--click", default="")
    ap.add_argument("--fill", default="", help="selector::value")
    ap.add_argument("--js", default="", help="extra JS to evaluate after load")
    ap.add_argument("--pre-js", default="", help="JS to evaluate before actions")
    ap.add_argument("--steps", default="", help='JSON list: [{"click":sel}|{"fill":[sel,val]}|{"js":expr}|{"wait":sec}]')
    ap.add_argument("--nolog", action="store_true")
    args = ap.parse_args()

    from libs.miniplaywright import launch

    SHOTS.mkdir(parents=True, exist_ok=True)
    outcome = {"name": args.name, "ok": False}
    with launch(headless=True, width=1440, height=1000) as browser:
        page = browser.page
        page.cdp.send("Page.addScriptToEvaluateOnNewDocument", {"source": INIT_SCRIPT})
        page.goto(args.url, timeout=30)
        time.sleep(args.wait)
        before = page.evaluate(SNAPSHOT_JS)
        action_desc = f"打开 {args.url}"
        observed_extra = ""
        if args.pre_js:
            try:
                page.evaluate(args.pre_js)
            except Exception as exc:  # noqa: BLE001
                observed_extra += f" | pre-js失败：{exc}"
        if args.steps:
            steps = json.loads(args.steps)
            done = []
            for item in steps:
                try:
                    if "click" in item:
                        page.click(item["click"], timeout=8)
                        done.append(f"点击 {item['click']}")
                        time.sleep(item.get("after", 1.2))
                    elif "fill" in item:
                        sel, value = item["fill"]
                        page.fill(sel, value, timeout=8)
                        done.append(f"输入 {sel}={value[:40]!r}")
                        time.sleep(item.get("after", 0.8))
                    elif "js" in item:
                        done.append(f"js={page.evaluate(item['js'])}")
                        time.sleep(item.get("after", 0.5))
                    elif "wait" in item:
                        time.sleep(item["wait"])
                except Exception as exc:  # noqa: BLE001
                    done.append(f"步骤失败 {item}: {exc}")
                    observed_extra += f" | 步骤失败：{exc}"
            action_desc = f"在 {before.get('url')} 执行：" + " → ".join(done)
        if args.click:
            action_desc = f"在 {before.get('url')} 点击 {args.click}"
            try:
                page.click(args.click, timeout=8)
                time.sleep(1.5)
            except Exception as exc:  # noqa: BLE001
                observed_extra = f"点击失败：{exc}"
        if args.fill:
            sel, _, value = args.fill.partition("::")
            action_desc = f"在 {before.get('url')} 向 {sel} 输入 {value!r}"
            try:
                page.fill(sel, value, timeout=8)
                time.sleep(0.8)
            except Exception as exc:  # noqa: BLE001
                observed_extra = f"输入失败：{exc}"
        if args.js:
            try:
                observed_extra += f" | js={page.evaluate(args.js)}"
            except Exception as exc:  # noqa: BLE001
                observed_extra += f" | js失败：{exc}"
        after = page.evaluate(SNAPSHOT_JS)
        shot = SHOTS / f"{args.name}.png"
        page.screenshot(shot)
        judgment, reason = judge(before if (args.click or args.fill or args.steps) else None, after, "click" if (args.click or args.steps) else ("fill" if args.fill else "goto"))
        if observed_extra:
            judgment, reason = "疑似", observed_extra
        entry = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "step": args.name,
            "action": action_desc,
            "url": after.get("url"),
            "title": after.get("title"),
            "observed": (after.get("bodyText") or "")[:500],
            "extras": observed_extra,
            "judgment": judgment,
            "judgment_reason": reason,
            "severity": "",
            "screenshot": f"screenshots/{args.name}.png",
            "console": (after.get("probe", {}).get("errors") or [])[:15],
            "failed_requests": (after.get("probe", {}).get("net") or [])[:15],
            "items": after.get("items"),
            "links": after.get("links"),
        }
        if not args.nolog:
            with LOG.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        outcome.update({"ok": True, "entry": entry, "before_body": (before or {}).get("bodyText", "")[:1500] if (args.click or args.fill) else ""})
        print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
