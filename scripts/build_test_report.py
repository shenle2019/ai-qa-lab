"""Build the 2026-11-03 CRUD test report from test function names."""

from __future__ import annotations

import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "docs" / "portfolio" / "test-report-2026-11-03.md"
OUT_HTML = ROOT / "docs" / "portfolio" / "test-report-2026-11-03.html"

SUITES = [
    (
        "接口 CRUD",
        ROOT / "suites" / "api" / "tests" / "test_tickets_crud.py",
        29,
        "pytest suites/api -q",
        "56 passed",
    ),
    (
        "Web UI CRUD",
        ROOT / "libs" / "miniplaywright" / "demo" / "test_sut_crud.py",
        28,
        "python -m libs.minipytest libs/miniplaywright/demo",
        "33 passed",
    ),
    (
        "App UI",
        ROOT / "libs" / "miniappium" / "tests" / "test_settings_suite.py",
        24,
        "pytest libs/miniappium/tests -q",
        "29 passed",
    ),
    (
        "测试平台 CRUD",
        ROOT / "apps" / "sut" / "backend" / "tests" / "test_platform_crud.py",
        26,
        "pytest apps/sut/backend -q",
        "38 passed",
    ),
]

GROUPS = [
    ("create", "创建"),
    ("get", "查询单条"),
    ("list", "列表"),
    ("update", "更新"),
    ("delete", "删除"),
    ("filter", "筛选"),
    ("search", "搜索"),
    ("run", "执行"),
    ("import", "导入"),
    ("patch", "更新"),
    ("open", "打开页面"),
    ("navigate", "页面导航"),
    ("home", "首页元素"),
    ("missing", "不存在"),
    ("invalid", "非法输入"),
    ("duplicate", "重复数据"),
    ("empty", "空值/空更新"),
    ("second", "多条数据"),
    ("long", "边界长度"),
    ("screenshot", "截图"),
    ("swipe", "滑动"),
    ("back", "返回"),
    ("current", "当前页面"),
    ("model", "设备信息"),
    ("serial", "设备序列号"),
    ("search_wifi", "搜索流程"),
    ("seed", "演示数据"),
]


def names(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return re.findall(r"^def (test_[a-zA-Z0-9_]+)\(", text, flags=re.MULTILINE)


def group(name: str) -> str:
    for prefix, label in GROUPS:
        if name.startswith(f"test_{prefix}") or f"_{prefix}_" in name:
            return label
    return "其他"


def main() -> None:
    total_new = sum(item[2] for item in SUITES)
    lines = [
        "# 2026-11-03 测试报告：CRUD 与分层用例扩充",
        "",
        "> 目标：每个子项新增 20+ 用例，覆盖创建、读取、更新、删除和关键交互。",
        "> 所有用例均本地真实运行，不使用 mock 数据替代被测系统。",
        "",
        "## 1. 汇总",
        "",
        "| 子项 | 新增 | 套件总数 | 命令 | 结果 |",
        "|---|---:|---:|---|---|",
    ]
    for title, _path, count, command, result in SUITES:
        lines.append(f"| {title} | {count} | — | `{command}` | {result} |")
    lines += [
        "",
        f"- 本轮新增：**{total_new}** 个用例。",
        "- 真实 pytest：172 个（接口 56 + 后端/平台 38 + 迷你 pytest 33 + 迷你 Playwright 6 + 迷你 Appium 29 + 迷你压测 5 + LLM 评测 5）。",
        "- 迷你演示：58 个（迷你 pytest 20 + Web 33 + App 3 + 压测 1 + 评测 1）。",
        "",
        "## 2. 接口 CRUD（29 个新增）",
        "",
        "覆盖：创建默认值、优先级、空描述、200/201 字标题、422 拒绝、读取/404、列表倒序、状态/优先级更新、非法枚举、空更新、删除/404/重复删除。",
        "",
        "| # | 用例 | 覆盖点 |",
        "|---:|---|---|",
    ]
    for index, name in enumerate(names(SUITES[0][1]), 1):
        lines.append(f"| {index} | `{name}` | {group(name)} |")

    lines += [
        "",
        "## 3. Web UI CRUD（28 个新增）",
        "",
        "覆盖：页面加载、创建（最小/描述/高/低优先级）、取消、空标题校验、200 字标题、列表可见、状态/优先级更新、删除、搜索、状态/优先级筛选、7 个页面导航。",
        "",
        "| # | 用例 | 覆盖点 |",
        "|---:|---|---|",
    ]
    for index, name in enumerate(names(SUITES[1][1]), 1):
        lines.append(f"| {index} | `{name}` | {group(name)} |")

    lines += [
        "",
        "## 4. App UI（24 个新增）",
        "",
        "覆盖：Settings 首页 9 个元素、7 个页面打开/返回、返回首页、搜索 Wi-Fi、滑动、截图、当前 Activity、Home 后重启。",
        "",
        "| # | 用例 | 覆盖点 |",
        "|---:|---|---|",
    ]
    for index, name in enumerate(names(SUITES[2][1]), 1):
        lines.append(f"| {index} | `{name}` | {group(name)} |")

    lines += [
        "",
        "## 5. 测试平台 CRUD（26 个新增）",
        "",
        "覆盖：项目创建/重复/列表/404、用例创建/筛选/非法项目、计划创建/筛选/404、执行通过/失败/404、结果查询、缺陷创建/更新/筛选/非法状态、报告导入、汇总字段。",
        "",
        "| # | 用例 | 覆盖点 |",
        "|---:|---|---|",
    ]
    for index, name in enumerate(names(SUITES[3][1]), 1):
        lines.append(f"| {index} | `{name}` | {group(name)} |")

    lines += [
        "",
        "## 6. 复现命令",
        "",
        "```bash",
        "cd /e/ailearning/ai-qa-lab",
        "./.venv/Scripts/python.exe -m pytest suites/api -q",
        "./.venv/Scripts/python.exe -m pytest apps/sut/backend -q",
        "./.venv/Scripts/python.exe -m pytest libs/miniappium/tests -q",
        "./.venv/Scripts/python.exe -m libs.minipytest libs/miniplaywright/demo",
        "```",
        "",
        "## 7. 边界",
        "",
        "- App 用例跑在本机 Android 模拟器；CI 无设备时自动 skip。",
        "- Web 用例跑在本机 Edge headless；CI 无 Chromium 时自动 skip。",
        "- 接口和平台用例使用临时/内存 SQLite，不污染开发数据。",
        "- 本轮新增以 CRUD 和关键交互为主，不代表生产级覆盖率。",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    html = markdown.markdown(
        OUT_MD.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "toc"],
    )
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>测试报告 2026-11-03</title>
<style>
:root{{color-scheme:dark;--bg:#0b1120;--panel:#111a2e;--line:#26344d;--text:#e5edf8;--muted:#8fa3bf;--accent:#38bdf8}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:14px/1.7 "Segoe UI","Microsoft YaHei",sans-serif}}
.wrap{{max-width:1100px;margin:0 auto;padding:32px 24px 64px}}
h1{{font-size:28px}}h2{{margin-top:32px;font-size:20px;border-top:1px solid var(--line);padding-top:16px}}
table{{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:12.5px}}
th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{color:var(--muted)}}tr:last-child td{{border-bottom:0}}
code{{background:rgba(56,189,248,.1);color:#bae6fd;padding:1px 5px;border-radius:5px;font-family:Consolas,monospace}}
pre{{background:#0a0f1c;border:1px solid var(--line);border-radius:10px;padding:12px;overflow:auto}}
blockquote{{color:var(--muted);border-left:3px solid var(--accent);margin:12px 0;padding-left:12px}}
a{{color:var(--accent)}}footer{{margin-top:36px;color:var(--muted);font-size:12px}}
</style></head><body><div class="wrap">{html}
<footer>AI全栈测试开发平台-shenle · 2026-11-03 · 离线报告</footer></div></body></html>"""
    OUT_HTML.write_text(page, encoding="utf-8")
    print(f"built: {OUT_MD}")
    print(f"built: {OUT_HTML}")


if __name__ == "__main__":
    main()
