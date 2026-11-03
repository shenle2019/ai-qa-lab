"""JSON and offline HTML reports for LLM evaluation."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .engine import METRIC_NAMES, EvalResult

SCHEMA_VERSION = "1.0"
TOOL_VERSION = "0.1.0"


def result_to_dict(result: EvalResult, comparison: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "minieval", "version": TOOL_VERSION},
        "started_at": result.started_at,
        "judge": result.judge,
        "threshold": result.threshold,
        "passed": result.passed,
        "summary": result.summary,
        "failures": result.failures,
        "cases": result.cases,
        "comparison": comparison,
    }


def write_json_report(result: EvalResult, path: Path | str, comparison: dict[str, Any] | None = None) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result_to_dict(result, comparison), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target


def _escape(value: Any) -> str:
    return html.escape(str(value))


CSS = """
:root{color-scheme:dark;--bg:#0b1120;--panel:#111a2e;--line:#26344d;--text:#e5edf8;--muted:#8fa3bf;
--pass:#34d399;--fail:#f87171;--accent:#38bdf8;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.6 "Segoe UI",Arial,sans-serif}
.wrap{max-width:1120px;margin:0 auto;padding:32px 24px 64px}h1{margin:0;font-size:26px}
.sub{color:var(--muted);margin:6px 0 0}.meta{color:var(--muted);font-size:12px;text-align:right}
header{display:flex;justify-content:space-between;gap:20px;align-items:flex-end;margin-bottom:22px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card .n{font-size:24px;font-weight:700}.card .l{color:var(--muted);font-size:12px}
.card.pass .n{color:var(--pass)}.card.fail .n{color:var(--fail)}
h2{margin:30px 0 12px;font-size:18px}table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);font-size:12px}
tr:last-child td{border-bottom:0}.badge{display:inline-block;border-radius:999px;padding:2px 8px;font-size:11px;font-weight:700}
.badge.pass{background:rgba(52,211,153,.12);color:var(--pass)}.badge.fail{background:rgba(248,113,113,.12);color:var(--fail)}
.bar{display:grid;grid-template-columns:160px 1fr 60px;gap:10px;align-items:center;margin:8px 0}
.bar .track{height:10px;background:#0a0f1c;border:1px solid var(--line);border-radius:999px;overflow:hidden}
.bar .fill{height:100%;background:linear-gradient(90deg,var(--accent),#22d3ee)}
pre{background:#0a0f1c;border:1px solid var(--line);border-radius:8px;padding:10px;overflow:auto;white-space:pre-wrap}
.muted{color:var(--muted)}footer{margin-top:36px;color:var(--muted);font-size:12px}
.delta-pos{color:var(--pass)}.delta-neg{color:var(--fail)}
@media(max-width:760px){header{display:block}.meta{text-align:left;margin-top:10px}}
"""


def _metric_bars(summary: dict[str, float]) -> str:
    parts = []
    for key in METRIC_NAMES:
        value = summary.get(key, 0.0)
        parts.append(
            f'<div class="bar"><span>{_escape(key)}</span>'
            f'<div class="track"><div class="fill" style="width:{value * 100:.1f}%"></div></div>'
            f'<span>{value:.2f}</span></div>'
        )
    return "".join(parts)


def _comparison_block(comparison: dict[str, Any] | None) -> str:
    if not comparison:
        return ""
    rows = []
    for key in METRIC_NAMES:
        delta = comparison["delta"].get(key, 0.0)
        cls = "delta-pos" if delta > 0 else "delta-neg" if delta < 0 else "muted"
        rows.append(
            f"<tr><td>{_escape(key)}</td><td>{comparison['baseline'][key]:.2f}</td>"
            f"<td>{comparison['candidate'][key]:.2f}</td>"
            f'<td class="{cls}">{delta:+.2f}</td></tr>'
        )
    return (
        "<h2>Baseline vs candidate</h2>"
        '<table><thead><tr><th>Metric</th><th>Baseline</th><th>Candidate</th><th>Delta</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _html_page(result: EvalResult, comparison: dict[str, Any] | None) -> str:
    status = "PASS" if result.passed else "FAIL"
    status_class = "pass" if result.passed else "fail"
    cards = [
        (status_class, "status", status),
        ("", "judge", result.judge),
        ("", "cases", len(result.cases)),
        ("", "threshold", f"{result.threshold:.2f}"),
        ("", "overall", f"{result.summary['overall']:.2f}"),
        ("", "failures", len(result.failures)),
    ]
    card_html = "".join(
        f'<div class="card {_escape(cls)}"><div class="n">{_escape(value)}</div><div class="l">{_escape(label)}</div></div>'
        for cls, label, value in cards
    )
    rows = []
    for item in result.cases:
        scores = item["scores"]
        ok = scores["overall"] >= result.threshold
        rows.append(
            f'<tr><td>{_escape(item["id"])}</td><td>{_escape(item["input"])}</td>'
            f'<td>{_escape(item["actual_output"])}</td>'
            f'<td>{scores["overall"]:.2f}</td>'
            f'<td><span class="badge {"pass" if ok else "fail"}">{"PASS" if ok else "FAIL"}</span></td></tr>'
        )
    failures = (
        "<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in result.failures) + "</ul>"
        if result.failures
        else '<p class="muted">No case below threshold.</p>'
    )
    return (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>minieval report · {_escape(result.started_at)}</title>"
        f"<style>{CSS}</style></head><body><div class=\"wrap\">"
        f"<header><div><h1>minieval report</h1><p class=\"sub\">LLM evaluation · dataset · judge · metrics · thresholds</p></div>"
        f"<div class=\"meta\">judge: {_escape(result.judge)}<br>threshold: {result.threshold:.2f}<br>{_escape(result.started_at)}</div></header>"
        f"<div class=\"cards\">{card_html}</div>"
        "<h2>Metrics</h2>"
        f"{_metric_bars(result.summary)}"
        f"{_comparison_block(comparison)}"
        "<h2>Cases</h2>"
        "<table><thead><tr><th>ID</th><th>Input</th><th>Actual output</th><th>Overall</th><th>Status</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        "<h2>Failures</h2>"
        f"{failures}"
        f"<footer>minieval {TOOL_VERSION} · offline report, no CDN</footer>"
        "</div></body></html>"
    )


def write_html_report(result: EvalResult, path: Path | str, comparison: dict[str, Any] | None = None) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_html_page(result, comparison), encoding="utf-8")
    return target
