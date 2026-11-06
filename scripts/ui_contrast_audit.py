"""Contrast audit for the Citrus Lab theme.

Walks every page, every element that renders text, and reports text whose
computed colour is too close to its effective background. This is how the
dark-theme leftovers (``#cbd5e1`` on white and friends) get found without
eyeballing thirty screenshots.

Usage:
    python scripts/ui_contrast_audit.py            # all pages
    UI_AUDIT_MIN=3.0 python scripts/ui_contrast_audit.py
"""

import json
import os
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get("UI_BASE", "http://127.0.0.1:8000/ui/")
MIN = float(os.environ.get("UI_AUDIT_MIN", "3.0"))
PAGES = [
    ("projects", "#/projects"),
    ("overview", "#/overview"),
    ("requirements", "#/requirements"),
    ("functional", "#/functional"),
    ("kb", "#/kb"),
    ("api", "#/api-automation"),
    ("ui", "#/ui-automation"),
    ("users", "#/users"),
    ("system-ai", "#/system-ai"),
    ("environments", "#/environments"),
    ("modules", "#/modules"),
    ("members", "#/members"),
    ("ai-logs", "#/ai-logs"),
    ("tools", "#/tools"),
]

AUDIT_JS = r"""
(min) => {
  // 纯装饰性字形：面包屑分隔符，本来就该比正文淡
  const DECORATIVE = ['crumb-sep'];
  const parse = (c) => {
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map((v) => parseFloat(v));
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const lum = ({ r, g, b }) => {
    const f = (v) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const bgOf = (el) => {
    let node = el;
    const stack = [];
    while (node && node !== document.documentElement) {
      const c = parse(getComputedStyle(node).backgroundColor);
      if (c && c.a > 0.9) return c;
      if (c && c.a > 0) stack.push(c);
      node = node.parentElement;
    }
    return { r: 255, g: 255, b: 255, a: 1 };
  };
  const out = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  let node;
  while ((node = walker.nextNode())) {
    const text = node.textContent.trim();
    if (!text) continue;
    const el = node.parentElement;
    if (!el || seen.has(el)) continue;
    if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(el.tagName)) continue;
    seen.add(el);
    const style = getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none') continue;
    if (DECORATIVE.some((c) => el.classList.contains(c))) continue;
    const rect = el.getBoundingClientRect();
    if (rect.width < 4 || rect.height < 4) continue;
    if (parseFloat(style.opacity) < 0.5) continue;
    const fg = parse(style.color);
    if (!fg) continue;
    const bg = bgOf(el);
    const l1 = lum(fg);
    const l2 = lum(bg);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    if (ratio >= min) continue;
    out.push({
      tag: el.tagName.toLowerCase(),
      cls: String(el.className || '').slice(0, 60),
      text: text.slice(0, 40),
      color: style.color,
      bg: `rgb(${bg.r}, ${bg.g}, ${bg.b})`,
      ratio: Math.round(ratio * 100) / 100,
      size: style.fontSize,
      weight: style.fontWeight,
    });
  }
  return out;
}
"""


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    total = 0
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except Exception:
            browser = playwright.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        for name, path in PAGES:
            page.goto(BASE + path, wait_until="load")
            page.wait_for_timeout(1400)
            rows = page.evaluate(AUDIT_JS, MIN)
            if not rows:
                continue
            total += len(rows)
            print(f"\n== {name} ({len(rows)}) ==")
            for row in rows:
                print(
                    f"  {row['ratio']:>4} :1  {row['tag']}.{row['cls']}  "
                    f"color={row['color']} bg={row['bg']} {row['size']}/{row['weight']}  «{row['text']}»"
                )
        browser.close()
    print(f"\nTOTAL low-contrast text nodes: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
