"""JSON and self-contained HTML reports for load results."""

from __future__ import annotations

import html
import json
import platform
import sys
from pathlib import Path
from typing import Any

from .engine import LoadResult

SCHEMA_VERSION = "1.0"
TOOL_VERSION = "0.1.0"


def _histogram(latencies: list[float]) -> list[dict[str, Any]]:
    buckets = [
        ("0-50 ms", 0, 50),
        ("50-100 ms", 50, 100),
        ("100-200 ms", 100, 200),
        ("200-500 ms", 200, 500),
        ("500-1000 ms", 500, 1000),
        ("1000+ ms", 1000, float("inf")),
    ]
    result = []
    for label, low, high in buckets:
        count = sum(1 for value in latencies if low <= value < high)
        result.append({"label": label, "count": count})
    return result


def result_to_dict(result: LoadResult) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "miniload", "version": TOOL_VERSION},
        "started_at": result.started_at,
        "environment": {"python": platform.python_version(), "platform": sys.platform},
        "scenario": {
            "name": result.scenario.name,
            "method": result.scenario.method,
            "url": result.scenario.url,
            "headers": result.scenario.headers,
            "think_time": result.scenario.think_time,
        },
        "config": {
            "vus": result.vus,
            "duration": result.duration,
            "ramp_up": result.ramp_up,
            "thresholds": result.thresholds,
        },
        "summary": {
            "total": result.total,
            "success": result.success,
            "errors": result.errors,
            "error_rate": result.error_rate,
            "rps": result.rps,
            "elapsed": result.elapsed,
            "passed": result.passed,
        },
        "percentiles": result.percentiles,
        "status_counts": result.status_counts,
        "error_messages": result.error_messages,
        "violations": result.violations,
        "histogram": _histogram(result.latencies_ms),
    }


def write_json_report(result: LoadResult, path: Path | str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def _escape(value: Any) -> str:
    return html.escape(str(value))


CSS = """
:root{color-scheme:dark;--bg:#0b1120;--panel:#111a2e;--line:#26344d;--text:#e5edf8;--muted:#8fa3bf;
--pass:#34d399;--fail:#f87171;--accent:#38bdf8;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.6 "Segoe UI",Arial,sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:32px 24px 64px}h1{margin:0;font-size:26px}
.sub{color:var(--muted);margin:6px 0 0}.meta{color:var(--muted);font-size:12px;text-align:right}
header{display:flex;justify-content:space-between;gap:20px;align-items:flex-end;margin-bottom:22px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card .n{font-size:26px;font-weight:700}.card .l{color:var(--muted);font-size:12px}
.card.pass .n{color:var(--pass)}.card.fail .n{color:var(--fail)}
h2{margin:30px 0 12px;font-size:18px}table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line)}th{color:var(--muted);font-size:12px}
tr:last-child td{border-bottom:0}.badge{display:inline-block;border-radius:999px;padding:2px 8px;font-size:11px;font-weight:700}
.badge.pass{background:rgba(52,211,153,.12);color:var(--pass)}.badge.fail{background:rgba(248,113,113,.12);color:var(--fail)}
.bar{display:grid;grid-template-columns:120px 1fr 60px;gap:10px;align-items:center;margin:8px 0}
.bar .track{height:10px;background:#0a0f1c;border:1px solid var(--line);border-radius:999px;overflow:hidden}
.bar .fill{height:100%;background:linear-gradient(90deg,var(--accent),#22d3ee)}
pre{background:#0a0f1c;border:1px solid var(--line);border-radius:8px;padding:10px;overflow:auto;white-space:pre-wrap}
.muted{color:var(--muted)}footer{margin-top:36px;color:var(--muted);font-size:12px}
@media(max-width:760px){header{display:block}.meta{text-align:left;margin-top:10px}}
"""


def _html_page(result: LoadResult) -> str:
    status = "PASS" if result.passed else "FAIL"
    status_class = "pass" if result.passed else "fail"
    cards = [
        ("", "total requests", result.total),
        ("", "RPS", f"{result.rps:.1f}"),
        ("", "p95 latency", f"{result.percentiles['p95']} ms"),
        (status_class, "error rate", f"{result.error_rate:.2%}"),
        (status_class, "thresholds", status),
    ]
    card_html = "".join(
        f'<div class="card {_escape(cls)}"><div class="n">{_escape(value)}</div><div class="l">{_escape(label)}</div></div>'
        for cls, label, value in cards
    )
    percentile_rows = "".join(
        f"<tr><td>{_escape(key)}</td><td>{_escape(value)} ms</td></tr>"
        for key, value in result.percentiles.items()
    )
    status_rows = (
        "".join(
            f"<tr><td>{_escape(key)}</td><td>{_escape(value)}</td></tr>"
            for key, value in sorted(result.status_counts.items())
        )
        or '<tr><td colspan="2" class="muted">no responses</td></tr>'
    )
    error_rows = (
        "".join(
            f"<tr><td>{_escape(key)}</td><td>{_escape(value)}</td></tr>"
            for key, value in sorted(result.error_messages.items(), key=lambda item: -item[1])
        )
        or '<tr><td colspan="2" class="muted">no errors</td></tr>'
    )
    histogram = _histogram(result.latencies_ms)
    max_count = max((item["count"] for item in histogram), default=1) or 1
    histogram_html = "".join(
        f'<div class="bar"><span>{_escape(item["label"])}</span>'
        f'<div class="track"><div class="fill" style="width:{(item["count"] / max_count) * 100:.1f}%"></div></div>'
        f'<span>{_escape(item["count"])}</span></div>'
        for item in histogram
    )
    violations = (
        "<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in result.violations) + "</ul>"
        if result.violations
        else '<p class="muted">All thresholds passed.</p>'
    )
    meta = (
        f"scenario: {_escape(result.scenario.name)}<br>"
        f"{_escape(result.scenario.method)} {_escape(result.scenario.url)}<br>"
        f"vus: {result.vus} · duration: {result.duration}s · ramp-up: {result.ramp_up}s · elapsed: {result.elapsed}s"
    )
    return (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>miniload report · {_escape(result.started_at)}</title>"
        f"<style>{CSS}</style></head><body><div class=\"wrap\">"
        f"<header><div><h1>miniload report</h1><p class=\"sub\">Load test · thresholds · percentiles · offline HTML</p></div>"
        f"<div class=\"meta\">{meta}</div></header>"
        f"<div class=\"cards\">{card_html}</div>"
        "<h2>Thresholds</h2>"
        f'<div class="card {status_class}"><div class="l">status</div><div class="n">{_escape(status)}</div></div>'
        f"{violations}"
        "<h2>Percentiles</h2><table><thead><tr><th>Metric</th><th>Value</th></tr></thead>"
        f"<tbody>{percentile_rows}</tbody></table>"
        "<h2>Latency distribution</h2>"
        f"{histogram_html}"
        "<h2>Status codes</h2><table><thead><tr><th>Status</th><th>Count</th></tr></thead>"
        f"<tbody>{status_rows}</tbody></table>"
        "<h2>Top errors</h2><table><thead><tr><th>Error</th><th>Count</th></tr></thead>"
        f"<tbody>{error_rows}</tbody></table>"
        f"<footer>miniload {TOOL_VERSION} · generated {_escape(result.started_at)} · offline report, no CDN</footer>"
        "</div></body></html>"
    )


def write_html_report(result: LoadResult, path: Path | str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_html_page(result), encoding="utf-8")
    return target
