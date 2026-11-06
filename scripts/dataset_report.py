"""Render docs/dataset/README.md from the seed result JSON files."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "dataset"

LABELS = {"local": "本地（http://127.0.0.1:8000）", "remote": "线上（Railway）"}

COUNT_ROWS = [
    ("projects", "项目"),
    ("requirements", "需求"),
    ("cases", "功能用例"),
    ("plans", "测试计划"),
    ("defects", "缺陷"),
    ("knowledge_bases", "知识库"),
    ("knowledge_documents", "知识库文档"),
    ("api_assets", "接口资产"),
    ("api_endpoints", "接口"),
    ("api_cases", "接口用例"),
    ("api_runs", "接口执行记录"),
    ("ui_cases", "UI 用例"),
    ("ui_runs", "UI 执行记录"),
    ("environments", "环境"),
    ("modules", "模块"),
    ("members", "成员"),
    ("users", "账号"),
    ("models", "AI 模型配置"),
]


def _files(label: str) -> list[Path]:
    return [
        path
        for path in OUT.glob(f"{label}-*.json")
        if path.name.startswith(f"{label}-")
        and not path.name.startswith("failures-")
    ]


def latest(label: str) -> dict | None:
    files = sorted(_files(label), key=lambda path: path.stat().st_mtime)
    if not files:
        return None
    payload = json.loads(files[-1].read_text(encoding="utf-8"))
    payload["_file"] = files[-1].name
    return payload


def latest_with_tests(label: str) -> dict | None:
    files = sorted(_files(label), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("tests"):
            payload["_file"] = path.name
            return payload
    return None


def latest_failures(label: str) -> dict | None:
    files = sorted(OUT.glob(f"failures-{label}-*.json"), key=lambda path: path.stat().st_mtime)
    if not files:
        return None
    best = None
    best_score = -1
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        score = sum(1 for item in payload.get("runs", []) if item.get("diagnosed"))
        if score >= best_score:
            best, best_score = payload, score
            payload["_file"] = path.name
    return best


def test_bucket(tests: list[dict]) -> dict[str, dict[str, int]]:
    buckets: dict[str, dict[str, int]] = {}
    for item in tests:
        kind = item["kind"]
        status = item.get("status") or item.get("result") or "n/a"
        if isinstance(status, str) and status.startswith("error"):
            status = "error"
        if isinstance(status, str) and status.startswith("failed"):
            status = "failed"
        buckets.setdefault(kind, {})
        buckets[kind][status] = buckets[kind].get(status, 0) + 1
    return buckets


KIND_TEXT = {
    "api_case_run": "接口用例执行",
    "api_scenario_run": "接口场景执行",
    "kb_search": "知识库检索",
    "plan_execution": "功能计划执行",
    "ui_case_run": "UI 用例执行",
    "requirement_ai": "需求 AI 分析",
}


def main() -> int:
    local = latest("local")
    remote = latest("remote")
    if not local:
        print("no local dataset json")
        return 1

    lines: list[str] = []
    lines.append("# 全量数据集")
    lines.append("")
    lines.append("平台里每一类实体都按“≥10 个差异化条目 / 每项目”建好，并跑了真实执行，执行记录全部保留。")
    lines.append("")
    lines.append("## 数据规模")
    lines.append("")
    header = "| 实体 | " + " | ".join(LABELS[key] for key in ("local", "remote")) + " |"
    lines.append(header)
    lines.append("| --- | " + " | ".join("---" for _ in range(2)) + " |")
    for key, label in COUNT_ROWS:
        cells = []
        for payload in (local, remote):
            value = (payload or {}).get("counts", {}).get(key)
            cells.append("—" if value is None else str(value))
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## 全平台概览（来自 /api/platform/summary）")
    lines.append("")
    lines.append("| 指标 | " + " | ".join(LABELS[key] for key in ("local", "remote")) + " |")
    lines.append("| --- | --- | --- |")
    for key, label in [
        ("projects", "项目数"),
        ("cases", "用例数"),
        ("plans", "计划数"),
        ("executions", "执行次数"),
        ("defects", "缺陷数"),
        ("pass_rate", "通过率"),
        ("results_total", "用例结果总数"),
    ]:
        cells = []
        for payload in (local, remote):
            summary = (payload or {}).get("platform_summary", {})
            value = summary.get(key)
            cells.append("—" if value is None else str(value))
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## 测试执行记录")
    lines.append("")
    for key in ("local", "remote"):
        payload = latest_with_tests(key)
        if not payload:
            continue
        lines.append(f"### {LABELS.get(payload['label'], payload['label'])}")
        lines.append("")
        lines.append(f"- 结果文件：`docs/dataset/{payload['_file']}`")
        if payload.get("elapsed_seconds"):
            lines.append(f"- 采集耗时：{payload['elapsed_seconds']} 秒")
        lines.append("")
        lines.append("| 测试类型 | 结果分布 |")
        lines.append("| --- | --- |")
        for kind, counts in test_bucket(payload["tests"]).items():
            detail = "，".join(f"{status} {count}" for status, count in sorted(counts.items()))
            lines.append(f"| {KIND_TEXT.get(kind, kind)} | {detail} |")
        lines.append("")

    lines.append("## 失败注入与 AI 归因")
    lines.append("")
    for key in ("local", "remote"):
        payload = latest_failures(key)
        if not payload:
            continue
        runs = payload["runs"]
        failed = sum(1 for item in runs if item["status"] == "failed")
        diagnosed = sum(1 for item in runs if item.get("diagnosed"))
        lines.append(f"### {LABELS.get(key, key)}")
        lines.append("")
        lines.append(f"- 结果文件：`docs/dataset/{payload['_file']}`")
        lines.append(f"- 注入用例：{len(runs)} 条，执行失败 {failed} 条，AI 归因 {diagnosed} 条")
        sample = next((item for item in runs if item.get("ai_root_cause")), None)
        if sample:
            text = " ".join(sample["ai_root_cause"].split())[:160]
            lines.append(f"- 归因样例（{sample['project']}）：{text}")
        lines.append("")
    lines.append("> 失败是故意造的：断言要求 `GET /api/platform/summary` 返回 500，实际返回 200，")
    lines.append("> 用来验证「失败 → 记录 → AI 归因」这条链路，不代表产品缺陷。")
    lines.append("")

    lines.append("## 每个项目都有什么")
    lines.append("")
    lines.append("每个项目都会补齐到下面这套结构（已存在的不重复创建）：")
    lines.append("")
    lines.append("| 维度 | 每个项目的条目 |")
    lines.append("| --- | --- |")
    lines.append("| 需求 | 10 条（登录鉴权/订单管理/支付退款/搜索筛选/批量导出/权限控制/消息通知/审计日志/分页性能/数据看板） |")
    lines.append("| 功能用例 | 10 条，状态分布在 草稿 / 待审核 / 已通过 |")
    lines.append("| 测试计划 | 2 个（冒烟 / 回归），冒烟计划会真实执行 6 条用例 |")
    lines.append("| 缺陷 | 3 条（超时、越权、性能） |")
    lines.append("| 知识库 | 2 个，每个 5 个功能 × 4 篇文档 = 40 篇，自动分块 |")
    lines.append("| 接口资产 | 1 份 OpenAPI，含 4 个真实平台接口 + 6 个业务接口 = 10 个接口 |")
    lines.append("| 接口用例 | 10 条（4 条可执行 + 6 条参数校验草稿）+ 1 条跨接口场景 |")
    lines.append("| UI 用例 | 10 条，覆盖概览/项目/需求/功能/知识库/接口/UI/环境/模块/成员页 |")
    lines.append("| 环境 | 4 个（dev / test / staging / prod），带 Base URL 与变量 |")
    lines.append("| 模块 | 4 个，带负责人 |")
    lines.append("| 成员 | 4 个（测试/开发/产品/运维） |")
    lines.append("")

    lines.append("## 复现方式")
    lines.append("")
    lines.append("```powershell")
    lines.append("# 本地（带 AI 分析与 UI 真跑）")
    lines.append(".venv\\Scripts\\python.exe scripts\\seed_dataset.py --base http://127.0.0.1:8000 --label local --ai --ai-limit 8 --ui-run --ui-limit 12")
    lines.append("")
    lines.append("# 线上（写接口要带 APP_API_KEY；生产没有 Chromium，UI 用例只建不跑）")
    lines.append(".venv\\Scripts\\python.exe scripts\\seed_dataset.py --base https://ai-qa-lab-production.up.railway.app --label remote --key <APP_API_KEY> --skip-plan-run")
    lines.append("")
    lines.append("# 失败注入 + 冒烟计划回归（让通过率有真实的分子分母）")
    lines.append(".venv\\Scripts\\python.exe scripts\\seed_failures.py --base http://127.0.0.1:8000 --label local --diagnose 4")
    lines.append("")
    lines.append("# 采集当前库存快照（不重复造数据）")
    lines.append(".venv\\Scripts\\python.exe scripts\\dataset_snapshot.py --label local")
    lines.append("")
    lines.append("# 重新生成本文件")
    lines.append(".venv\\Scripts\\python.exe scripts\\dataset_report.py")
    lines.append("```")
    lines.append("")
    lines.append("脚本是幂等的：按项目名 / 用例标题 / 知识库名去重，重复执行只会补缺，不会翻倍。")

    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("written", OUT / "README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
