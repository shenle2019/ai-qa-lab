"""JSON and self-contained HTML report writers."""

from __future__ import annotations

import html
import json
import platform
import sys
from pathlib import Path
from typing import Any

from .model import CaseResult, Failure, RunResult

SCHEMA_VERSION = "1.0"
TOOL_VERSION = "0.1.0"


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return repr(value)


def _failure_to_dict(failure: Failure | None) -> dict[str, Any] | None:
    if failure is None:
        return None
    return {
        "message": failure.message,
        "type": failure.type,
        "phase": failure.phase,
        "location": failure.location,
        "traceback": failure.traceback,
        "expected": _jsonable(failure.expected),
        "actual": _jsonable(failure.actual),
        "diff": failure.diff,
    }


def _case_to_dict(result: CaseResult) -> dict[str, Any]:
    case = result.case
    return {
        "id": case.nodeid,
        "module": case.path.name,
        "path": case.path.as_posix(),
        "class": case.class_name,
        "name": case.name,
        "params": _jsonable(case.params),
        "markers": [mark.name for mark in case.marks],
        "status": result.status,
        "phase": result.phase,
        "duration_ms": round(result.duration_ms, 3),
        "attempts": [
            {
                "number": attempt.number,
                "status": attempt.status,
                "duration_ms": round(attempt.duration_ms, 3),
                "failure": _failure_to_dict(attempt.failure),
            }
            for attempt in result.attempts
        ],
        "failure": _failure_to_dict(result.failure),
        "skip_reason": result.skip_reason,
        "xfail_reason": result.xfail_reason,
        "fixtures": [
            {
                "name": timing.name,
                "scope": timing.scope,
                "phase": timing.phase,
                "duration_ms": round(timing.duration_ms, 3),
                "status": timing.status,
            }
            for timing in result.fixtures
        ],
        "teardown_errors": [_failure_to_dict(item) for item in result.teardown_errors],
    }


def result_to_dict(result: RunResult) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "minipytest", "version": TOOL_VERSION},
        "started_at": result.started_at,
        "duration_ms": round(result.duration_ms, 3),
        "rootdir": result.rootdir.as_posix(),
        "command": result.command,
        "environment": {"python": platform.python_version(), "platform": sys.platform},
        "summary": result.summary,
        "tests": [_case_to_dict(item) for item in result.tests],
        "collection_errors": [
            {"path": error.path, "message": error.message, "traceback": error.traceback}
            for error in result.collection_errors
        ],
        "finalization_errors": [_failure_to_dict(item) for item in result.finalization_errors],
    }


def write_json_report(result: RunResult, path: Path | str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result_to_dict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target


def _escape(value: Any) -> str:
    return html.escape(str(value))


def _status_class(status: str) -> str:
    return {
        "passed": "pass",
        "failed": "fail",
        "error": "error",
        "skipped": "skip",
        "xfailed": "xfail",
        "xpassed": "xpass",
    }.get(status, "unknown")


def _failure_block(failure: Failure) -> str:
    parts = [
        '<div class="failure">',
        f'<div class="failure-head"><span class="badge {_status_class(failure.phase)}">{_escape(failure.phase)}</span>'
        f'<strong>{_escape(failure.type)}</strong>'
        f'<span class="location">{_escape(failure.location)}</span></div>',
        f'<p class="message">{_escape(failure.message)}</p>',
    ]
    if failure.expected is not None or failure.actual is not None:
        parts.append('<div class="values">')
        parts.append(f'<div><span>expected</span><pre>{_escape(failure.expected)}</pre></div>')
        parts.append(f'<div><span>actual</span><pre>{_escape(failure.actual)}</pre></div>')
        parts.append("</div>")
    if failure.diff:
        parts.append(f'<pre class="diff">{_escape(failure.diff)}</pre>')
    if failure.traceback:
        parts.append(f'<details><summary>traceback</summary><pre>{_escape(failure.traceback)}</pre></details>')
    parts.append("</div>")
    return "".join(parts)


def _case_row(result: CaseResult) -> str:
    case = result.case
    attempts = len(result.attempts)
    retry = f'<span class="retry">{attempts} attempts</span>' if attempts > 1 else ""
    return (
        f'<tr data-status="{_escape(result.status)}">'
        f'<td><span class="badge {_status_class(result.status)}">{_escape(result.status.upper())}</span></td>'
        f'<td class="nodeid">{_escape(case.nodeid)}</td>'
        f'<td>{result.duration_ms:.1f} ms</td>'
        f'<td>{retry}</td>'
        f"</tr>"
    )


def _failure_section(result: RunResult) -> str:
    blocks: list[str] = []
    for item in result.tests:
        if item.status in {"failed", "error"}:
            blocks.append(
                f'<section class="case-failure"><h3>{_escape(item.case.nodeid)}</h3>'
                f"{_failure_block(item.failure) if item.failure else ''}"
            )
            for teardown in item.teardown_errors:
                blocks.append(_failure_block(teardown))
            blocks.append("</section>")
    for error in result.collection_errors:
        blocks.append(
            f'<section class="case-failure"><h3>collection: {_escape(error.path)}</h3>'
            f'<p class="message">{_escape(error.message)}</p>'
            f'<details><summary>traceback</summary><pre>{_escape(error.traceback)}</pre></details></section>'
        )
    for failure in result.finalization_errors:
        blocks.append(
            f'<section class="case-failure"><h3>finalization</h3>{_failure_block(failure)}</section>'
        )
    if not blocks:
        return '<p class="empty">No failures or errors.</p>'
    return "".join(blocks)


CSS = """
:root{color-scheme:dark;--bg:#0b1120;--panel:#111a2e;--line:#26344d;--text:#e5edf8;--muted:#8fa3bf;
--pass:#34d399;--fail:#f87171;--error:#fb923c;--skip:#fbbf24;--xfail:#a78bfa;--xpass:#22d3ee;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.6 "Segoe UI",Arial,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:32px 24px 64px}
header{display:flex;justify-content:space-between;gap:20px;align-items:flex-end;margin-bottom:24px}
h1{margin:0;font-size:26px}h2{margin:34px 0 12px;font-size:18px}h3{margin:0 0 10px;font-size:14px;color:var(--muted)}
.sub{color:var(--muted);margin:6px 0 0}.meta{color:var(--muted);font-size:12px;text-align:right}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:20px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card .n{font-size:24px;font-weight:700}.card .l{color:var(--muted);font-size:12px}
.card.pass .n{color:var(--pass)}.card.fail .n{color:var(--fail)}.card.error .n{color:var(--error)}
.card.skip .n{color:var(--skip)}.card.xfail .n{color:var(--xfail)}.card.xpass .n{color:var(--xpass)}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}
button{background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:8px;padding:6px 12px;cursor:pointer}
button:hover,button.active{border-color:#4f7cff;background:#17233d}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-size:12px;font-weight:600}tr:last-child td{border-bottom:0}
.nodeid{font-family:Consolas,monospace;font-size:12px;word-break:break-all}
.badge{display:inline-block;border-radius:999px;padding:2px 8px;font-size:11px;font-weight:700;letter-spacing:.04em}
.badge.pass{background:rgba(52,211,153,.12);color:var(--pass)}.badge.fail{background:rgba(248,113,113,.12);color:var(--fail)}
.badge.error{background:rgba(251,146,60,.12);color:var(--error)}.badge.skip{background:rgba(251,191,36,.12);color:var(--skip)}
.badge.xfail{background:rgba(167,139,250,.12);color:var(--xfail)}.badge.xpass{background:rgba(34,211,238,.12);color:var(--xpass)}
.retry{color:var(--skip);font-size:11px}.case-failure{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin:12px 0}
.failure{border-left:3px solid var(--fail);padding-left:12px;margin:10px 0}
.failure-head{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.location{color:var(--muted);font-size:12px;font-family:Consolas,monospace}
.message{color:#fecaca;margin:8px 0}.values{display:grid;grid-template-columns:1fr 1fr;gap:10px}.values span{color:var(--muted);font-size:11px}
pre{background:#0a0f1c;border:1px solid var(--line);border-radius:8px;padding:10px;overflow:auto;white-space:pre-wrap;word-break:break-word}
.diff{color:#cbd5e1}.empty{color:var(--muted)}footer{margin-top:40px;color:var(--muted);font-size:12px}
@media(max-width:760px){.values{grid-template-columns:1fr}header{display:block}.meta{text-align:left;margin-top:10px}}
"""

SCRIPT = """
document.querySelectorAll('[data-filter]').forEach(function(btn){
  btn.addEventListener('click', function(){
    document.querySelectorAll('[data-filter]').forEach(function(b){b.classList.remove('active')});
    btn.classList.add('active');
    var f = btn.getAttribute('data-filter');
    document.querySelectorAll('tbody tr').forEach(function(row){
      var show = f === 'all' || row.getAttribute('data-status') === f;
      row.style.display = show ? '' : 'none';
    });
  });
});
"""


def _html_page(result: RunResult) -> str:
    summary = result.summary
    cards = [
        ("total", "total", summary.get("total", 0)),
        ("pass", "passed", summary.get("passed", 0)),
        ("fail", "failed", summary.get("failed", 0)),
        ("error", "errors", summary.get("error", 0)),
        ("skip", "skipped", summary.get("skipped", 0)),
        ("xfail", "xfailed", summary.get("xfailed", 0)),
        ("xpass", "xpassed", summary.get("xpassed", 0)),
        ("", "duration", f"{result.duration_ms / 1000:.2f}s"),
    ]
    card_html = "".join(
        f'<div class="card {_escape(cls)}"><div class="n">{_escape(value)}</div><div class="l">{_escape(label)}</div></div>'
        for cls, label, value in cards
    )
    rows = "".join(_case_row(item) for item in result.tests)
    command = " ".join(result.command)
    meta = (
        f"rootdir: {_escape(result.rootdir)}<br>"
        f"command: {_escape(command)}<br>"
        f"python: {_escape(platform.python_version())} · {_escape(sys.platform)}"
    )
    return (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>minipytest report · {_escape(result.started_at)}</title>"
        f"<style>{CSS}</style></head><body><div class=\"wrap\">"
        f"<header><div><h1>minipytest report</h1><p class=\"sub\">Mini pytest · collection, fixtures, params, markers, retry</p></div>"
        f"<div class=\"meta\">{meta}</div></header>"
        f"<div class=\"cards\">{card_html}</div>"
        "<h2>Failures and errors</h2>"
        f"{_failure_section(result)}"
        "<h2>All cases</h2>"
        "<div class=\"toolbar\">"
        "<button data-filter=\"all\" class=\"active\">All</button>"
        "<button data-filter=\"passed\">Passed</button>"
        "<button data-filter=\"failed\">Failed</button>"
        "<button data-filter=\"error\">Errors</button>"
        "<button data-filter=\"skipped\">Skipped</button>"
        "</div>"
        "<table><thead><tr><th>Status</th><th>Node ID</th><th>Duration</th><th>Attempts</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        f"<footer>minipytest {TOOL_VERSION} · generated {_escape(result.started_at)} · offline report, no CDN</footer>"
        f"<script>{SCRIPT}</script></div></body></html>"
    )


def write_html_report(result: RunResult, path: Path | str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_html_page(result), encoding="utf-8")
    return target
