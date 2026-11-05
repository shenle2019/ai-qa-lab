"""Scenario driver for the 2026-11-05 exploratory pass.

Runs a list of read-only / reversible scenarios in one browser session and
appends evidence to docs/explore/2026-11-05/log.jsonl.

Safety: every write path exercised here is known to return 401 in production
(verified with a `{}` POST before the run). No scenario submits a valid payload
with a key present; no scenario confirms a delete.

Usage: python scripts/explore_2026_11_05_scenarios.py --only ticket,knowledge
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
sys.path.insert(0, str(ROOT / "scripts"))

from explore_2026_11_05 import INIT_SCRIPT, SNAPSHOT_JS, LOG, SHOTS  # noqa: E402

BASE = "https://ai-qa-lab-production.up.railway.app/ui/#"

CLICK_TEXT_JS = """
([text, idx, exact]) => {
  const clean = v => String(v || '').replace(/\\s+/g, ' ').trim();
  const els = [...document.querySelectorAll('button,a,[role="button"],option,label,span')]
    .filter(el => {
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
    })
    .filter(el => exact ? clean(el.innerText || el.value) === text : clean(el.innerText || el.value).includes(text));
  const el = els[idx || 0];
  if (!el) return { ok: false, count: 0 };
  el.scrollIntoView({ block: 'center' });
  el.click();
  return { ok: true, count: els.length, text: clean(el.innerText || el.value).slice(0, 80), tag: el.tagName };
}
"""

FILL_PLACEHOLDER_JS = """
([hint, value]) => {
  const el = [...document.querySelectorAll('input,textarea')]
    .find(e => (e.getAttribute('placeholder') || '').includes(hint));
  if (!el) return { ok: false };
  el.focus();
  el.value = value;
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  return { ok: true, tag: el.tagName, len: el.value.length };
}
"""

FILL_SELECTOR_JS = """
([sel, value]) => {
  const el = document.querySelector(sel);
  if (!el) return { ok: false };
  el.focus(); el.value = value;
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  return { ok: true, tag: el.tagName, len: el.value.length };
}
"""

SELECT_BY_INDEX_JS = """
([scopeSel, index, value]) => {
  const scope = document.querySelector(scopeSel);
  if (!scope) return { ok: false, reason: 'no scope' };
  const el = scope.querySelectorAll('select')[index];
  if (!el) return { ok: false, reason: 'no select' };
  el.value = value;
  el.dispatchEvent(new Event('change', { bubbles: true }));
  return { ok: true, value: el.value, options: [...el.options].map(o => o.text) };
}
"""

COUNTER_JS = """
() => {
  const el = [...document.querySelectorAll('span,p,div')].find(e => /\\d+\\s*\\/\\s*\\d+\\s*条/.test(e.innerText || ''));
  return el ? el.innerText.trim().slice(0, 60) : null;
}
"""

SCENARIOS = [
    # ---------- 工单管理 ----------
    {
        "name": "020-ticket-create-empty",
        "url": f"{BASE}/tickets",
        "steps": [
            {"click_text": ["新建工单"]},
            {"wait": 0.8},
            {"click_text": ["创建", 0, True]},
            {"wait": 0.8},
            {"js": "(() => { const e=[...document.querySelectorAll('.alert.error')].map(x=>x.innerText.trim()); return {alerts:e, url:location.hash}; })()"},
        ],
    },
    {
        "name": "021-ticket-create-no-key",
        "url": f"{BASE}/tickets",
        "steps": [
            {"click_text": ["新建工单"]},
            {"wait": 0.5},
            {"fill_placeholder": ["一句话描述问题", "探索测试请勿创建"]},
            {"click_text": ["创建", 0, True]},
            {"wait": 2.0},
            {"js": "(() => ({url: location.hash, hasKey: !!localStorage.getItem('sut_api_key'), alerts: [...document.querySelectorAll('.alert,.error')].map(e=>e.innerText.trim()).slice(0,5), body: document.body.innerText.slice(0,300)}))()"},
        ],
    },
    {
        "name": "022-ticket-edit-empty-title",
        "url": f"{BASE}/tickets",
        "steps": [
            {"click_text": ["编辑", 0, True]},
            {"wait": 0.8},
            {"js": "(() => { const i=[...document.querySelectorAll('.modal input')][0]; if(!i) return 'no input'; i.value=''; i.dispatchEvent(new Event('input',{bubbles:true})); return 'cleared'; })()"},
            {"click_text": ["保存", 0, True]},
            {"wait": 0.8},
            {"js": "(() => ({alerts:[...document.querySelectorAll('.alert.error')].map(e=>e.innerText.trim()), url:location.hash}))()"},
        ],
    },
    {
        "name": "023-ticket-delete-confirm",
        "url": f"{BASE}/tickets",
        "pre_js": "window.__confirmMsg=null; window.confirm=(m)=>{window.__confirmMsg=m; return false;};",
        "steps": [
            {"js": "(() => ({before: document.querySelectorAll('tbody tr').length}))()"},
            {"click_text": ["删除", 0, True]},
            {"wait": 0.8},
            {"js": "(() => ({confirmMsg: window.__confirmMsg, rows: document.querySelectorAll('tbody tr').length}))()"},
        ],
    },
    {
        "name": "024-ticket-search-3000",
        "url": f"{BASE}/tickets",
        "steps": [
            {"fill_placeholder": ["搜索标题或描述", "A" * 3000]},
            {"wait": 1.0},
            {"js": "(() => ({counter: (window.__c=null, [...document.querySelectorAll('span')].map(e=>e.innerText.trim()).find(t=>/\\d+\\s*\\/\\s*\\d+\\s*条/.test(t)) || null), empty: document.body.innerText.includes('没有匹配的工单'), url: location.hash}))()"},
        ],
    },
    {
        "name": "025-ticket-search-special",
        "url": f"{BASE}/tickets",
        "steps": [
            {"fill_placeholder": ["搜索标题或描述", "<script>alert(1)</script>' OR '1'='1 😀"]},
            {"wait": 1.0},
            {"js": "(() => ({empty: document.body.innerText.includes('没有匹配的工单'), injected: document.body.innerHTML.includes('<script>alert(1)</script>'), url: location.hash}))()"},
        ],
    },
    {
        "name": "026-ticket-filter-closed",
        "url": f"{BASE}/tickets",
        "steps": [
            {"select_by_index": [".filters", 0, "closed"]},
            {"wait": 1.0},
            {"js": "(() => ({counter:[...document.querySelectorAll('span')].map(e=>e.innerText.trim()).find(t=>/\\d+\\s*\\/\\s*\\d+\\s*条/.test(t)) || null, rows: document.querySelectorAll('tbody tr').length, statuses:[...document.querySelectorAll('tbody .status-badge, tbody td:nth-child(4) select')].map(e=>e.value||e.innerText.trim()).slice(0,12)}))()"},
        ],
    },
    {
        "name": "027-ticket-double-click",
        "url": f"{BASE}/tickets",
        "steps": [
            {"click_text": ["新建工单"]},
            {"wait": 0.4},
            {"click_text": ["创建", 0, True]},
            {"click_text": ["创建", 0, True]},
            {"wait": 0.6},
            {"js": "(() => ({alerts:[...document.querySelectorAll('.alert.error')].map(e=>e.innerText.trim()), url:location.hash}))()"},
        ],
    },
    # ---------- 访问密钥 ----------
    {
        "name": "030-login-save-empty",
        "url": f"{BASE}/login",
        "steps": [
            {"click_text": ["保存", 0, True]},
            {"wait": 1.2},
            {"js": "(() => ({url: location.hash, savedMsg: document.body.innerText.includes('已保存'), key: localStorage.getItem('sut_api_key')}))()"},
        ],
    },
    {
        "name": "031-login-save-whitespace",
        "url": f"{BASE}/login",
        "steps": [
            {"fill_placeholder": ["粘贴服务端配置的访问密钥", "   "]},
            {"click_text": ["保存", 0, True]},
            {"wait": 1.2},
            {"js": "(() => ({url: location.hash, key: JSON.stringify(localStorage.getItem('sut_api_key'))}))()"},
        ],
    },
    # ---------- 知识库 ----------
    {
        "name": "040-knowledge-submit-no-key",
        "url": f"{BASE}/knowledge",
        "steps": [
            {"fill_placeholder": ["输入你要问知识库的问题", "工单如何升级优先级？"]},
            {"click_text": ["提交问题", 0, True]},
            {"wait": 2.0},
            {"js": "(() => ({url: location.hash, key: !!localStorage.getItem('sut_api_key'), body: document.body.innerText.slice(0,200)}))()"},
        ],
    },
    # ---------- API 工作台 ----------
    {
        "name": "050-workbench-send-no-key",
        "url": f"{BASE}/workbench",
        "steps": [
            {"click_text": ["发送", 0, True]},
            {"wait": 2.0},
            {"js": "(() => ({url: location.hash, key: !!localStorage.getItem('sut_api_key')}))()"},
        ],
    },
    {
        "name": "051-workbench-runall-no-key",
        "url": f"{BASE}/workbench",
        "steps": [
            {"click_text": ["运行全部", 0, True]},
            {"wait": 2.0},
            {"js": "(() => ({url: location.hash, key: !!localStorage.getItem('sut_api_key')}))()"},
        ],
    },
    {
        "name": "052-workbench-blank-url",
        "url": f"{BASE}/workbench",
        "steps": [
            {"fill_selector": [".request-url", ""]},
            {"click_text": ["发送", 0, True]},
            {"wait": 1.5},
            {"js": "(() => ({url: location.hash, body: document.body.innerText.slice(0,300)}))()"},
        ],
    },
    # ---------- 测试平台 ----------
    {
        "name": "060-platform-empty-project",
        "url": f"{BASE}/platform",
        "steps": [
            {"fill_placeholder": ["项目名称", ""]},
            {"click_text": ["新建项目", 0, True]},
            {"wait": 1.5},
            {"js": "(() => ({url: location.hash, alerts:[...document.querySelectorAll('.alert,.error')].map(e=>e.innerText.trim()).slice(0,5)}))()"},
        ],
    },
    # ---------- 测试用例 ----------
    {
        "name": "070-testcases-search-3000",
        "url": f"{BASE}/testcases",
        "steps": [
            {"fill_placeholder": ["搜索用例名", "Z" * 3000]},
            {"wait": 1.0},
            {"js": "(() => ({counter:[...document.querySelectorAll('span')].map(e=>e.innerText.trim()).find(t=>/\\d+\\s*\\/\\s*\\d+\\s*条/.test(t)) || null, empty: document.body.innerText.includes('没有匹配'), groups: document.querySelectorAll('.category, .case-group').length}))()"},
        ],
    },
    {
        "name": "071-testcases-filter-fail",
        "url": f"{BASE}/testcases",
        "steps": [
            {"select_by_index": [".toolbar", 0, "fail"]},
            {"wait": 1.0},
            {"js": "(() => ({body: document.body.innerText.slice(0,400), url: location.hash}))()"},
        ],
    },
    # ---------- 模型中心 ----------
    {
        "name": "080-models-empty-save",
        "url": f"{BASE}/models",
        "steps": [
            {"click_text": ["保存模型", 0, True]},
            {"wait": 1.5},
            {"js": "(() => ({url: location.hash, alerts:[...document.querySelectorAll('.alert,.error')].map(e=>e.innerText.trim()).slice(0,5)}))()"},
        ],
    },
    # ---------- 全局 ----------
    {
        "name": "090-unknown-route",
        "url": f"{BASE}/nope-not-exist",
        "steps": [{"wait": 1.0}],
    },
    {
        "name": "028-create-modal-mask-discard",
        "url": f"{BASE}/tickets",
        "steps": [
            {"click_text": ["新建工单"]},
            {"wait": 0.5},
            {"fill_placeholder": ["一句话描述问题", "我填了一半的内容"]},
            {"js": "(() => { const m=document.querySelector('.modal-mask'); m.click(); return 'mask clicked'; })()"},
            {"wait": 0.6},
            {"js": "(() => ({modalOpen: !!document.querySelector('.modal'), reopen: (document.querySelector('.btn') && true)}))()"},
            {"click_text": ["新建工单"]},
            {"wait": 0.6},
            {"js": "(() => { const i=[...document.querySelectorAll('.modal input')][0]; return {titleValue: i ? i.value : null, modalOpen: !!document.querySelector('.modal')}; })()"},
        ],
    },
    {
        "name": "029-edit-modal-mask-discard",
        "url": f"{BASE}/tickets",
        "steps": [
            {"click_text": ["编辑", 0, True]},
            {"wait": 0.6},
            {"js": "(() => { const i=[...document.querySelectorAll('.modal input')][0]; window.__orig=i.value; i.value='改到一半'; i.dispatchEvent(new Event('input',{bubbles:true})); return window.__orig; })()"},
            {"js": "(() => { document.querySelector('.modal-mask').click(); return 'mask clicked'; })()"},
            {"wait": 0.6},
            {"click_text": ["编辑", 0, True]},
            {"wait": 0.6},
            {"js": "(() => { const i=[...document.querySelectorAll('.modal input')][0]; return {orig: window.__orig, now: i ? i.value : null}; })()"},
        ],
    },
    {
        "name": "078-testcases-category-filter",
        "url": f"{BASE}/testcases",
        "steps": [
            {"click_text": ["性能测试"]},
            {"wait": 1.0},
            {"js": "(() => ({counter:[...document.querySelectorAll('span')].map(e=>e.innerText.trim()).find(t=>/\d+\s*\/\s*\d+\s*条/.test(t)) || null, active:[...document.querySelectorAll('.active')].map(e=>e.innerText.trim()).slice(0,3)}))()"},
        ],
    },
    {
        "name": "079-ticket-title-maxlength",
        "url": f"{BASE}/tickets",
        "steps": [
            {"click_text": ["新建工单"]},
            {"wait": 0.5},
            {"fill_placeholder": ["一句话描述问题", "超" * 500]},
            {"js": "(() => { const i=[...document.querySelectorAll('.modal input')][0]; return {len: i.value.length, max: i.getAttribute('maxlength')}; })()"},
        ],
    },
    {
        "name": "032-fake-key-create",
        "url": f"{BASE}/tickets",
        "pre_js": "localStorage.setItem('sut_api_key','wrong-key-123');",
        "steps": [
            {"click_text": ["新建工单"]},
            {"wait": 0.4},
            {"fill_placeholder": ["一句话描述问题", "探索测试请勿创建"]},
            {"click_text": ["创建", 0, True]},
            {"wait": 2.0},
            {"js": "(() => ({url: location.hash, key: localStorage.getItem('sut_api_key'), alerts:[...document.querySelectorAll('.alert,.error')].map(e=>e.innerText.trim()).slice(0,5)}))()"},
        ],
    },
    {
        "name": "033-row-select-no-key",
        "url": f"{BASE}/tickets",
        "pre_js": "window.__alerts=[]; window.alert=(m)=>{window.__alerts.push(String(m));};",
        "steps": [
            {"js": "(() => { const s=document.querySelector('tbody select'); return {before: s.value, ticket: document.querySelector('tbody strong').innerText}; })()"},
            {"select_by_index": ["tbody", 0, "low"]},
            {"wait": 2.0},
            {"js": "(() => ({url: location.hash, key: localStorage.getItem('sut_api_key'), alerts: window.__alerts}))()"},
        ],
    },
    {
        "name": "041-dashboard-kb-no-key",
        "url": f"{BASE}/",
        "steps": [
            {"fill_placeholder": ["例如：工单如何升级优先级", "工单如何升级优先级？"]},
            {"click_text": ["查询", 0, True]},
            {"wait": 2.0},
            {"js": "(() => ({url: location.hash, key: !!localStorage.getItem('sut_api_key')}))()"},
        ],
    },
    {
        "name": "053-workbench-error-text",
        "url": f"{BASE}/workbench",
        "steps": [
            {"click_text": ["发送", 0, True]},
            {"wait": 1.5},
            {"js": "(() => ({url: location.hash, alerts: [...document.querySelectorAll('.alert.error')].map(e=>e.innerText.trim()), response: document.body.innerText.includes('发送请求后显示')}))()"},
        ],
    },
    {
        "name": "071b-testcases-filter-failed",
        "url": f"{BASE}/testcases",
        "steps": [
            {"select_by_index": [".toolbar", 0, "failed"]},
            {"wait": 1.0},
            {"js": "(() => ({counter:[...document.querySelectorAll('span')].map(e=>e.innerText.trim()).find(t=>/\\d+\\s*\\/\\s*\\d+\\s*条/.test(t)) || null, empty: document.body.innerText.includes('没有匹配的用例'), rows: document.querySelectorAll('.case-row, tbody tr').length}))()"},
        ],
    },
    {
        "name": "072-testcases-category-click",
        "url": f"{BASE}/testcases",
        "steps": [
            {"click_text": ["性能测试", 0, True]},
            {"wait": 1.0},
            {"js": "(() => ({counter:[...document.querySelectorAll('span')].map(e=>e.innerText.trim()).find(t=>/\\d+\\s*\\/\\s*\\d+\\s*条/.test(t)) || null, active: [...document.querySelectorAll('.active')].map(e=>e.innerText.trim()).slice(0,5)}))()"},
        ],
    },
    {
        "name": "073-testcases-report-link",
        "url": f"{BASE}/testcases",
        "steps": [
            {"js": "(() => { const a=[...document.querySelectorAll('a')].find(x=>x.innerText.includes('完整报告')); return a ? {href:a.getAttribute('href'), target:a.getAttribute('target')} : null; })()"},
        ],
    },
    {
        "name": "074-platform-sections",
        "url": f"{BASE}/platform",
        "steps": [
            {"js": "(() => ({text: document.body.innerText.slice(0,6000), buttons: [...document.querySelectorAll('button')].map(b=>b.innerText.trim()).filter(Boolean).slice(0,40)}))()"},
        ],
    },
    {
        "name": "075-header-refresh",
        "url": f"{BASE}/tickets",
        "steps": [
            {"click_text": ["刷新状态", 0, True]},
            {"js": "(() => ({btn: [...document.querySelectorAll('button')].map(b=>b.innerText.trim()).find(t=>t.includes('刷新')), alerts:[...document.querySelectorAll('.alert')].map(e=>e.innerText.trim()).slice(0,3)}))()"},
            {"wait": 1.5},
            {"js": "(() => ({btn: [...document.querySelectorAll('button')].map(b=>b.innerText.trim()).find(t=>t.includes('刷新')), rows: document.querySelectorAll('tbody tr').length}))()"},
        ],
    },
    {
        "name": "076-ticket-row-selects",
        "url": f"{BASE}/tickets",
        "steps": [
            {"js": "(() => { const s=[...document.querySelectorAll('tbody select')].slice(0,2); return s.map(x=>({value:x.value, title:x.getAttribute('title'), aria:x.getAttribute('aria-label'), cls:x.className})); })()"},
        ],
    },
    {
        "name": "077-login-long-key",
        "url": f"{BASE}/login",
        "steps": [
            {"fill_placeholder": ["粘贴服务端配置的访问密钥", "K" * 5000]},
            {"click_text": ["保存", 0, True]},
            {"wait": 1.2},
            {"js": "(() => ({url: location.hash, keyLen: (localStorage.getItem('sut_api_key')||'').length}))()"},
        ],
    },
    {
        "name": "092-mobile-tickets",
        "url": f"{BASE}/tickets",
        "steps": [
            {"viewport": [390, 844]},
            {"wait": 1.2},
            {"js": "(() => ({scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth, bodyWidth: document.body.scrollWidth, overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth, sidebar: !!document.querySelector('aside') && document.querySelector('aside').getBoundingClientRect().width}))()"},
        ],
    },
    {
        "name": "093-unknown-route-404",
        "url": f"{BASE}/nope-not-exist",
        "steps": [
            {"wait": 1.0},
            {"js": "(() => ({url: location.hash, mainText: (document.querySelector('main')||document.body).innerText.trim().slice(0,200), has404: /404|不存在|未找到/.test(document.body.innerText)}))()"},
        ],
    },
    {
        "name": "091-back-after-401",
        "url": f"{BASE}/tickets",
        "steps": [
            {"click_text": ["新建工单"]},
            {"wait": 0.4},
            {"fill_placeholder": ["一句话描述问题", "探索测试请勿创建"]},
            {"click_text": ["创建", 0, True]},
            {"wait": 1.8},
            {"js": "history.back(); 'back'"},
            {"wait": 1.5},
            {"js": "(() => ({url: location.hash, modalOpen: !!document.querySelector('.modal'), title: document.querySelector('.modal h2')?.innerText || null}))()"},
        ],
    },
]


def ev(page, fn_src: str, args):
    """Call a JS arrow function with JSON args (Page.evaluate has no arg param)."""
    return page.evaluate(f"({fn_src})({json.dumps(args, ensure_ascii=False)})")


def run(page, sc: dict) -> dict:
    # Same-hash navigation does not reload the SPA; force a fresh document so
    # modal/filter state from the previous scenario cannot leak in.
    page.goto("data:text/html,<title>blank</title>", timeout=15)
    time.sleep(0.3)
    page.goto(sc["url"], timeout=30)
    time.sleep(2.2)
    if sc.get("pre_js"):
        page.evaluate(sc["pre_js"])
    trace = []
    for st in sc.get("steps", []):
        try:
            if "click_text" in st:
                text, idx, exact = (st["click_text"] + [None, 0, False])[:3]
                r = ev(page, CLICK_TEXT_JS, [text, idx or 0, bool(exact)])
                trace.append(f"点击「{text}」→ {r}")
                time.sleep(1.0)
            elif "fill_placeholder" in st:
                hint, value = st["fill_placeholder"]
                r = ev(page, FILL_PLACEHOLDER_JS, [hint, value])
                trace.append(f"输入[{hint}] 长度={r.get('len')} → ok={r.get('ok')}")
                time.sleep(0.7)
            elif "fill_selector" in st:
                sel, value = st["fill_selector"]
                r = ev(page, FILL_SELECTOR_JS, [sel, value])
                trace.append(f"输入 {sel}={value[:40]!r} → {r}")
                time.sleep(0.7)
            elif "select_by_index" in st:
                scope, idx, value = st["select_by_index"]
                r = ev(page, SELECT_BY_INDEX_JS, [scope, idx, value])
                trace.append(f"选择 {scope} 第{idx}个={value} → {r}")
                time.sleep(0.9)
            elif "js" in st:
                r = page.evaluate(st["js"])
                trace.append(f"观察：{json.dumps(r, ensure_ascii=False)[:600]}")
            elif "viewport" in st:
                w, h = st["viewport"]
                page.set_viewport(w, h)
                trace.append(f"视口 {w}x{h}")
                time.sleep(0.5)
            elif "wait" in st:
                time.sleep(st["wait"])
        except Exception as exc:  # noqa: BLE001
            trace.append(f"步骤失败 {st}: {exc}")
    time.sleep(0.5)
    after = page.evaluate(SNAPSHOT_JS)
    shot = SHOTS / f"{sc['name']}.png"
    page.screenshot(shot)
    return {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "step": sc["name"],
        "action": " → ".join(trace[:20]),
        "url": after.get("url"),
        "title": after.get("title"),
        "observed": (after.get("bodyText") or "")[:600],
        "judgment": "待复核",
        "severity": "",
        "screenshot": f"screenshots/{sc['name']}.png",
        "console": (after.get("probe", {}).get("errors") or [])[:15],
        "failed_requests": (after.get("probe", {}).get("net") or [])[:15],
        "end_state": after.get("url"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    wanted = [s.strip() for s in args.only.split(",") if s.strip()]
    scenarios = [s for s in SCENARIOS if not wanted or any(w in s["name"] for w in wanted)]

    from libs.miniplaywright import launch

    SHOTS.mkdir(parents=True, exist_ok=True)
    with launch(headless=True, width=1440, height=1000) as browser:
        page = browser.page
        page.cdp.send("Page.addScriptToEvaluateOnNewDocument", {"source": INIT_SCRIPT})
        for sc in scenarios:
            entry = run(page, sc)
            with LOG.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(json.dumps({"step": entry["step"], "url": entry["url"], "action": entry["action"][:300]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
