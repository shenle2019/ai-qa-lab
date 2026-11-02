"""Archive the current project report as an immutable dated snapshot.

Usage:
    .venv/Scripts/python.exe scripts/archive_report.py \
        --version v0.2.0 --date 2026-11-02 \
        --tests 33 --pages 6 --modules 8 --replications 1

Creates docs/reports/<date>-<version>/ with:
    index.html      static snapshot (screenshot paths rewritten)
    report.md       Markdown report
    screenshots/    copied screenshots
    metrics.json    version, date, commit, counts
    README.md       snapshot note

Also regenerates docs/reports/index.html.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REPORTS = DOCS / "reports"
SHOTS = DOCS / "portfolio" / "screenshots"


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def write_snapshot(version: str, date: str, tests: int, pages: int, modules: int, replications: int, commit: str, force: bool) -> Path:
    name = f"{date}-{version}"
    out = REPORTS / name
    if out.exists() and not force:
        raise SystemExit(f"snapshot already exists: {out} (use --force to overwrite)")

    out.mkdir(parents=True, exist_ok=True)

    shutil.copy2(DOCS / "portfolio" / "project-report.md", out / "report.md")

    shot_out = out / "screenshots"
    shot_out.mkdir(exist_ok=True)
    for image in SHOTS.glob("*.png"):
        shutil.copy2(image, shot_out / image.name)

    learning_src = DOCS / "learning"
    if learning_src.exists():
        shutil.copytree(learning_src, out / "learning", dirs_exist_ok=True)

    html = (DOCS / "index.html").read_text(encoding="utf-8")
    html = html.replace("portfolio/screenshots/", "screenshots/")
    banner = (
        '<div style="margin:0 0 18px;padding:10px 14px;border:1px solid rgba(251,191,36,.35);'
        'border-radius:10px;color:#fde68a;background:rgba(251,191,36,.08);font-size:12px">'
        f'归档快照 · {date} · {version} · commit {commit} · '
        '<a href="../" style="color:#fde68a">返回归档索引</a></div>'
    )
    html = html.replace('<div class="wrap">', f'<div class="wrap">{banner}', 1)
    (out / "index.html").write_text(html, encoding="utf-8")

    metrics = {
        "version": version,
        "date": date,
        "git_commit": commit,
        "tests": tests,
        "pages": pages,
        "modules": modules,
        "replications": replications,
        "source_report": "docs/portfolio/project-report.md",
        "source_site": "docs/index.html",
        "learning_guide": "learning/" if (out / "learning").exists() else None,
    }
    (out / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    (out / "README.md").write_text(
        f"# 项目报告快照 {version}（{date}）\n\n"
        f"- 代码提交：`{commit}`\n"
        f"- 自动化测试：{tests}\n"
        f"- 页面：{pages}\n"
        f"- 模块：{modules}\n"
        f"- 复刻闭环：{replications}\n\n"
        "本目录是归档快照，不再修改。需要更正时新增 `corrections.md`，不要改历史文件。\n\n"
        "学习手册快照：`learning/index.html`（若本次快照包含）。\n\n"
        "在线访问：`https://shenle2019.github.io/ai-qa-lab/reports/"
        f"{name}/`\n",
        encoding="utf-8",
    )
    return out


def write_index() -> None:
    entries = []
    for folder in sorted(REPORTS.glob("*-v*"), reverse=True):
        metrics_file = folder / "metrics.json"
        if not metrics_file.exists():
            continue
        metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
        entries.append((folder.name, metrics))

    cards = []
    for name, metrics in entries:
        cards.append(
            f'<a class="card" href="./{name}/">'
            f'<div class="meta">{metrics["date"]} · {metrics["version"]}</div>'
            f'<strong>{name}</strong>'
            f'<div class="stats">{metrics["tests"]} tests · {metrics["pages"]} pages · '
            f'{metrics["modules"]} modules · {metrics["replications"]} replications</div>'
            f'<div class="commit">commit {metrics["git_commit"]}</div>'
            f"</a>"
        )

    body = "\n".join(cards) if cards else '<p class="empty">还没有归档快照。</p>'
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>AI QA Lab · 报告归档</title>
<style>
  :root {{ --bg:#070b14; --line:rgba(148,163,184,.16); --text:#e6edf7; --muted:#8fa1ba; --accent:#38bdf8; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:40px 22px 70px; color:var(--text); background:radial-gradient(900px 600px at 15% -10%, rgba(56,189,248,.16), transparent 60%), var(--bg); font-family:"Segoe UI","PingFang SC","Microsoft YaHei",system-ui,sans-serif; }}
  .wrap {{ max-width:980px; margin:0 auto; }}
  h1 {{ margin:0 0 8px; font-size:30px; letter-spacing:-.02em; }}
  p.lead {{ margin:0 0 26px; color:var(--muted); font-size:13px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:14px; }}
  .card {{ display:block; padding:18px; border:1px solid var(--line); border-radius:14px; color:var(--text); text-decoration:none; background:linear-gradient(180deg,rgba(17,29,51,.92),rgba(14,23,40,.94)); }}
  .card:hover {{ border-color:rgba(56,189,248,.4); }}
  .meta {{ color:var(--accent); font-size:11px; letter-spacing:.06em; text-transform:uppercase; }}
  .card strong {{ display:block; margin:8px 0 10px; font-size:15px; }}
  .stats {{ color:var(--muted); font-size:12px; }}
  .commit {{ margin-top:8px; color:rgba(143,161,186,.7); font-family:Consolas,monospace; font-size:11px; }}
  .empty {{ color:var(--muted); }}
  a.back {{ display:inline-block; margin-top:26px; color:var(--accent); font-size:12.5px; text-decoration:none; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>项目报告归档</h1>
  <p class="lead">按里程碑归档的不可变快照。日报在 docs/progress 中，不生成独立报告；每个模块/重大版本归档一次。</p>
  <div class="grid">{body}</div>
  <a class="back" href="../">← 返回最新报告</a>
</div>
</body>
</html>
"""
    (REPORTS / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True, help="e.g. v0.2.0")
    parser.add_argument("--date", required=True, help="e.g. 2026-11-02")
    parser.add_argument("--tests", type=int, default=0)
    parser.add_argument("--pages", type=int, default=0)
    parser.add_argument("--modules", type=int, default=0)
    parser.add_argument("--replications", type=int, default=0)
    parser.add_argument("--commit", default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    commit = args.commit or git_commit()
    out = write_snapshot(
        args.version,
        args.date,
        args.tests,
        args.pages,
        args.modules,
        args.replications,
        commit,
        args.force,
    )
    write_index()
    print(f"archived: {out}")
    print(f"index:    {REPORTS / 'index.html'}")


if __name__ == "__main__":
    main()
