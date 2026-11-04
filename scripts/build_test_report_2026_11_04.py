"""Run each expanded suite separately and generate the 2026-11-04 report."""

from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "docs" / "portfolio" / "test-report-2026-11-04.md"
OUT_HTML = ROOT / "docs" / "portfolio" / "test-report-2026-11-04.html"
OUT_JSON = ROOT / "docs" / "portfolio" / "test-cases.json"

CATEGORIES = OrderedDict(
    [
        ("接口测试", ("suites/api/tests/test_techniques.py", "api-techniques", "等价类 / 边界值 / 错误推测 / 场景法")),
        ("兼容性", ("suites/api/tests/test_compatibility.py", "compatibility", "协议 / 编码 / 格式 / 架构兼容")),
        ("可靠性", ("suites/api/tests/test_reliability.py", "reliability", "重复性 / 并发 / 恢复 / 隔离")),
        ("Web 测试", ("suites/web/tests", "web", "UI 等价类 / 边界 / 错误推测 / 场景")),
        ("性能测试", ("suites/perf/tests", "perf", "并发 / 持续负载 / 爬坡 / 阈值")),
        ("App 测试", ("suites/app/tests", "app", "元素解析 + 真机场景")),
    ]
)


def run_suite(path: str, slug: str) -> tuple[dict[str, list[dict]], str]:
    xml = ROOT / "docs" / "portfolio" / f"test-report-2026-11-04-{slug}.xml"
    command = [sys.executable, "-m", "pytest", path, "-q", f"--junitxml={xml}"]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8")
    if not xml.exists():
        print(result.stdout or "", result.stderr or "")
        raise SystemExit(f"pytest did not produce junit xml for {path}")
    tree = ET.parse(xml)
    cases = []
    for case in tree.iter("testcase"):
        cases.append(
            {
                "name": case.get("name", ""),
                "time": float(case.get("time", "0") or 0),
                "skipped": case.find("skipped") is not None,
                "failed": case.find("failure") is not None or case.find("error") is not None,
            }
        )
    passed = sum(1 for item in cases if not item["skipped"] and not item["failed"])
    skipped = sum(1 for item in cases if item["skipped"])
    failed = sum(1 for item in cases if item["failed"])
    summary = f"{passed} passed, {skipped} skipped"
    if failed:
        summary += f", {failed} failed"
    return {"cases": cases}, summary


def build_markdown(grouped: dict[str, list[dict]], summaries: dict[str, str]) -> str:
    all_cases = [item for items in grouped.values() for item in items]
    total = len(all_cases)
    passed = sum(1 for item in all_cases if not item["skipped"] and not item["failed"])
    skipped = sum(1 for item in all_cases if item["skipped"])
    failed = sum(1 for item in all_cases if item["failed"])

    lines = [
        "# 2026-11-04 测试用例扩充与执行报告",
        "",
        f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "> 执行方式：按类别分别运行 pytest，结果来自 JUnit XML。",
        "",
        "## 结论",
        "",
        f"六类场景共设计并收集 **{total}** 条用例：通过 {passed}，失败 {failed}，跳过 {skipped}。"
        + ("跳过项全部是 Android 真机/模拟器用例，当前环境没有可用设备，未伪造通过。" if skipped else ""),
        "",
        "| 类别 | 执行结果 |",
        "|---|---|",
    ]
    for label in grouped:
        lines.append(f"| {label} | `{summaries[label]}` |")

    lines += [
        "",
        "## 分类汇总",
        "",
        "| 类别 | 用例数 | 通过 | 跳过 | 失败 | 设计方法 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for label, items in grouped.items():
        p = sum(1 for item in items if not item["skipped"] and not item["failed"])
        s = sum(1 for item in items if item["skipped"])
        f = sum(1 for item in items if item["failed"])
        lines.append(f"| {label} | {len(items)} | {p} | {s} | {f} | {CATEGORIES[label][2]} |")

    lines += [
        "",
        "## 本次发现并修复",
        "",
        "- 超大路径 ID（如 24 位整数）会触发 SQLite 溢出并返回 500，已改为参数越界直接返回 404。",
        "- 执行器先开写事务再回调自身接口，会导致 `database is locked`；已在部署阶段修复为先执行后落库，并启用 WAL 与 30 秒 busy timeout。",
        "- 测试基础设施：多个 `tests` 目录没有包标记，pytest 混合收集时 `page`/`sut` fixture 会串到其他目录；已补 `__init__.py` 并把冲突 fixture 改为唯一名称。",
        "",
        "## 分类明细",
        "",
    ]
    for label, items in grouped.items():
        lines.append(f"### {label}（{len(items)} 条）")
        lines.append("")
        for item in items:
            mark = "[x]" if not item["skipped"] and not item["failed"] else ("[ ]" if item["failed"] else "[-]")
            suffix = "（跳过：无 Android 设备）" if item["skipped"] else ""
            lines.append(f"- {mark} `{item['name']}`{suffix}")
        lines.append("")
    return "\n".join(lines)


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>2026-11-04 测试用例扩充与执行报告 · AI全栈测试开发平台-shenle</title>
<style>
  :root {{ --bg:#070b14; --line:rgba(148,163,184,.16); --text:#e6edf7; --muted:#9fb0c9; --accent:#38bdf8; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:36px 20px 70px; color:var(--text); background:radial-gradient(900px 600px at 15% -10%, rgba(56,189,248,.16), transparent 60%), var(--bg); font-family:"Segoe UI","PingFang SC","Microsoft YaHei",system-ui,sans-serif; }}
  .wrap {{ max-width:1000px; margin:0 auto; }}
  h1 {{ font-size:28px; margin:0 0 8px; }}
  h2 {{ font-size:19px; margin:28px 0 10px; }}
  h3 {{ font-size:15px; margin:20px 0 8px; color:#bae6fd; }}
  p, li {{ color:#c9d6e8; font-size:13.5px; line-height:1.8; }}
  table {{ width:100%; border-collapse:collapse; margin:14px 0; font-size:12.5px; }}
  th, td {{ padding:9px 10px; border-bottom:1px solid rgba(148,163,184,.12); text-align:left; }}
  th {{ color:var(--muted); font-size:11px; letter-spacing:.05em; text-transform:uppercase; }}
  code {{ padding:2px 6px; border-radius:6px; color:#bae6fd; background:rgba(56,189,248,.1); font-family:Consolas,monospace; font-size:12px; }}
  blockquote {{ margin:12px 0; padding:10px 14px; border-left:3px solid var(--accent); color:var(--muted); background:rgba(56,189,248,.06); }}
</style>
</head>
<body>
<div class="wrap">
{body}
</div>
</body>
</html>
"""


def build_catalog(grouped: dict[str, list[dict]]) -> dict:
    categories = []
    for label, items in grouped.items():
        passed = sum(1 for item in items if not item["skipped"] and not item["failed"])
        skipped = sum(1 for item in items if item["skipped"])
        failed = sum(1 for item in items if item["failed"])
        categories.append(
            {
                "name": label,
                "method": CATEGORIES[label][2],
                "total": len(items),
                "passed": passed,
                "skipped": skipped,
                "failed": failed,
                "cases": [
                    {
                        "name": item["name"],
                        "status": "skipped" if item["skipped"] else ("failed" if item["failed"] else "passed"),
                        "duration_ms": round(item["time"] * 1000, 2),
                    }
                    for item in items
                ],
            }
        )
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total": sum(item["total"] for item in categories),
        "passed": sum(item["passed"] for item in categories),
        "skipped": sum(item["skipped"] for item in categories),
        "failed": sum(item["failed"] for item in categories),
        "report_url": "/portfolio/test-report-2026-11-04.html",
        "categories": categories,
    }


def main() -> None:
    grouped: dict[str, list[dict]] = OrderedDict()
    summaries: dict[str, str] = {}
    for label, (path, slug, _) in CATEGORIES.items():
        result, summary = run_suite(path, slug)
        grouped[label] = result["cases"]
        summaries[label] = summary
        print(f"{label}: {summary}")

    md = build_markdown(grouped, summaries)
    OUT_MD.write_text(md, encoding="utf-8")
    body = markdown.Markdown(extensions=["tables"]).convert(md)
    OUT_HTML.write_text(HTML_TEMPLATE.format(body=body), encoding="utf-8")
    catalog = build_catalog(grouped)
    OUT_JSON.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"built: {OUT_MD}")
    print(f"built: {OUT_HTML}")
    print(f"built: {OUT_JSON}")


if __name__ == "__main__":
    main()
