"""Render docs/learning/project-walkthrough.md to a public HTML page.

Usage:
    .venv/Scripts/python.exe scripts/build_learning_page.py
"""

from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "learning" / "project-walkthrough.md"
OUTPUT = ROOT / "docs" / "learning" / "index.html"

CSS = """
:root { --bg:#070b14; --panel:#0e1728; --line:rgba(148,163,184,.16); --text:#e6edf7; --muted:#9fb0c9; --accent:#38bdf8; --green:#34d399; --amber:#fbbf24; }
* { box-sizing:border-box; }
body { margin:0; color:var(--text); background:radial-gradient(1100px 700px at 15% -10%, rgba(56,189,248,.16), transparent 60%), var(--bg); font-family:"Segoe UI","PingFang SC","Microsoft YaHei",system-ui,sans-serif; line-height:1.8; }
.wrap { max-width:980px; margin:0 auto; padding:32px 22px 80px; }
.top { display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap; padding-bottom:18px; border-bottom:1px solid var(--line); font-size:12.5px; }
.top a { color:var(--accent); text-decoration:none; }
.banner { margin:18px 0 8px; padding:12px 16px; border:1px solid rgba(251,191,36,.32); border-radius:12px; color:#fde68a; background:rgba(251,191,36,.08); font-size:12.5px; }
h1 { margin:26px 0 10px; font-size:34px; line-height:1.25; letter-spacing:-.03em; }
h2 { margin:38px 0 12px; padding-top:18px; border-top:1px solid var(--line); font-size:23px; letter-spacing:-.02em; }
h3 { margin:24px 0 8px; font-size:16px; color:#bae6fd; }
h4 { margin:18px 0 6px; font-size:14px; color:#cbd5e1; }
p, li { color:#c9d6e8; font-size:14px; }
a { color:var(--accent); }
blockquote { margin:16px 0; padding:12px 16px; border-left:3px solid var(--accent); color:var(--muted); background:rgba(56,189,248,.06); }
code { padding:2px 6px; border-radius:6px; color:#bae6fd; background:rgba(56,189,248,.1); font-family:"Cascadia Code",Consolas,monospace; font-size:12px; }
pre { padding:16px; overflow:auto; border:1px solid var(--line); border-radius:12px; background:rgba(4,8,16,.65); }
pre code { padding:0; background:transparent; font-size:12px; line-height:1.65; }
table { width:100%; border-collapse:collapse; margin:16px 0; font-size:12.5px; }
th, td { padding:9px 10px; border-bottom:1px solid rgba(148,163,184,.12); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:10.5px; letter-spacing:.06em; text-transform:uppercase; }
.toc { margin:18px 0 26px; padding:16px 18px; border:1px solid var(--line); border-radius:12px; background:rgba(148,163,184,.04); }
.toc ul { margin:0; padding-left:18px; }
.toc li { margin:4px 0; font-size:12.5px; }
.toc a { text-decoration:none; }
hr { border:0; border-top:1px solid var(--line); margin:28px 0; }
@media (max-width:700px) { h1 { font-size:26px; } h2 { font-size:20px; } }
"""


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    converter = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc"],
        extension_configs={"toc": {"toc_depth": "2"}},
    )
    body = converter.convert("[TOC]\n\n" + text)
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>AI QA Lab · 项目学习手册</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <span>AI QA Lab · 项目学习手册 · v0.2.0</span>
    <span>
      <a href="../">最新报告</a> ·
      <a href="../reports/">归档索引</a> ·
      <a href="https://github.com/shenle2019/ai-qa-lab">GitHub</a>
    </span>
  </div>
  <div class="banner">这是给测试小白看的完整拆解：每一步做什么、为什么、涉及哪些名词、原理是什么、效果是什么。</div>
  {body}
</div>
</body>
</html>
"""
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"built: {OUTPUT}")


if __name__ == "__main__":
    main()
