"""Render a single execution as a standalone HTML report."""

from __future__ import annotations

import html
from datetime import datetime

from . import platform_models as models
from .timeutils import utcnow


def render(execution: models.TestExecution, results: list[models.TestResult]) -> str:
    total = execution.total or 0
    pass_rate = (execution.passed / total * 100) if total else 0.0
    status_class = "failed" if execution.failed else ("skipped" if execution.skipped and not execution.passed else "passed")

    rows = []
    for item in results:
        message = html.escape(item.message or "")
        rows.append(
            f"<tr><td>#{item.id}</td><td>{html.escape(item.case_name)}</td>"
            f'<td><span class="badge {html.escape(item.status)}">{html.escape(item.status)}</span></td>'
            f"<td>{item.duration_ms} ms</td>"
            f'<td class="msg">{message}</td></tr>'
        )
    if not rows:
        rows.append('<tr><td colspan="5" class="empty">没有结果明细</td></tr>')

    failed = [item for item in results if item.status in {"failed", "error"}]
    failure_block = ""
    if failed:
        items = "".join(
            f"<li><strong>{html.escape(item.case_name)}</strong>：{html.escape(item.message or '')}</li>"
            for item in failed
        )
        failure_block = f'<section class="card"><h2>失败原因</h2><ul>{items}</ul></section>'

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>执行报告 #{execution.id} · AI全栈测试开发平台-shenle</title>
<style>
  :root {{ --bg:#070b14; --panel:#0e1728; --line:rgba(148,163,184,.16); --text:#e6edf7; --muted:#9fb0c9; --accent:#38bdf8; --green:#34d399; --red:#f87171; --amber:#fbbf24; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:36px 20px 70px; color:var(--text); background:radial-gradient(900px 600px at 15% -10%, rgba(56,189,248,.16), transparent 60%), var(--bg); font-family:"Segoe UI","PingFang SC","Microsoft YaHei",system-ui,sans-serif; }}
  .wrap {{ max-width:1000px; margin:0 auto; }}
  h1 {{ margin:0 0 6px; font-size:26px; }}
  h2 {{ font-size:17px; margin:0 0 10px; }}
  .muted {{ color:var(--muted); font-size:12.5px; }}
  .metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:10px; margin:20px 0; }}
  .metric {{ padding:12px 14px; border:1px solid var(--line); border-radius:12px; background:rgba(14,23,40,.7); }}
  .metric span {{ display:block; color:var(--muted); font-size:11px; }}
  .metric strong {{ font-size:20px; }}
  .card {{ margin:16px 0; padding:16px 18px; border:1px solid var(--line); border-radius:14px; background:rgba(14,23,40,.6); }}
  table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
  th, td {{ padding:9px 10px; border-bottom:1px solid rgba(148,163,184,.12); text-align:left; vertical-align:top; }}
  th {{ color:var(--muted); font-size:10.5px; letter-spacing:.06em; text-transform:uppercase; }}
  .badge {{ padding:2px 8px; border-radius:999px; font-size:11px; }}
  .badge.passed {{ color:#a7f3d0; background:rgba(52,211,153,.14); }}
  .badge.failed, .badge.error {{ color:#fecaca; background:rgba(248,113,113,.16); }}
  .badge.skipped {{ color:#fde68a; background:rgba(251,191,36,.14); }}
  .empty {{ color:var(--muted); }}
  .msg {{ color:#fca5a5; }}
  ul {{ margin:0; padding-left:18px; color:#fecaca; font-size:12.5px; }}
</style>
</head>
<body>
<div class="wrap">
  <p class="muted">EXECUTION REPORT · 计划 #{execution.plan_id}</p>
  <h1>执行报告 #{execution.id} · <span class="badge {status_class}">{html.escape(execution.status)}</span></h1>
  <p class="muted">开始时间：{execution.started_at} · 总耗时：{execution.duration_ms} ms</p>

  <div class="metrics">
    <div class="metric"><span>总数</span><strong>{execution.total}</strong></div>
    <div class="metric"><span>通过</span><strong>{execution.passed}</strong></div>
    <div class="metric"><span>失败</span><strong>{execution.failed}</strong></div>
    <div class="metric"><span>跳过</span><strong>{execution.skipped}</strong></div>
    <div class="metric"><span>通过率</span><strong>{pass_rate:.1f}%</strong></div>
  </div>

  {failure_block}

  <section class="card">
    <h2>逐条结果</h2>
    <table>
      <thead><tr><th>ID</th><th>用例</th><th>状态</th><th>耗时</th><th>信息</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </section>

  <p class="muted">生成时间：{utcnow().isoformat(timespec="seconds")}Z · AI全栈测试开发平台-shenle</p>
</div>
</body>
</html>
"""
