"""Phase 1 end-to-end smoke test against a running SUT.

Run with the repo venv:
    .venv\\Scripts\\python.exe scripts\\phase1_smoke.py

It creates a requirement, runs the three requirement skills through the real
HTTP API (real model calls), and writes the result to
``docs/phases/phase-1/smoke-output.json`` for the test record.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parents[1] / "docs" / "phases" / "phase-1" / "smoke-output.json"

BODY = """# 工单列表增强

## 背景
客服反馈工单列表只能按页翻，找特定状态的工单很慢。

## 需求
1. 工单列表顶部增加状态筛选：全部 / 待处理 / 处理中 / 已关闭。
2. 支持按创建时间倒序、正序切换。
3. 增加「导出 CSV」按钮，导出当前筛选结果。
4. 导出超过 5000 条时需要提示，并改为后台任务，完成后站内信通知。

## 约束
- 只有管理员可以导出。
- 导出文件编码 UTF-8 BOM，Excel 打开不乱码。
"""


def main() -> int:
    report: dict = {"base": BASE, "steps": []}
    with httpx.Client(base_url=BASE, timeout=180.0) as client:
        health = client.get("/health")
        report["health"] = health.json()
        if health.status_code != 200:
            print("service not healthy", health.text)
            return 1

        projects = client.get("/api/platform/projects").json()
        if not projects:
            project = client.post(
                "/api/platform/projects",
                json={"name": "Phase1 冒烟项目", "description": "phase 1 smoke"},
            ).json()
        else:
            project = projects[0]
        report["project"] = {"id": project["id"], "name": project["name"]}

        created = client.post(
            "/api/platform/requirements",
            json={
                "project_id": project["id"],
                "title": "工单列表支持状态筛选、排序与 CSV 导出",
                "body": BODY,
                "priority": "high",
            },
        )
        report["steps"].append({"create": created.status_code})
        if created.status_code != 201:
            print("create failed", created.status_code, created.text)
            return 1
        requirement = created.json()
        report["requirement_id"] = requirement["id"]

        analysed = client.post(f"/api/platform/requirements/{requirement['id']}/analyze")
        report["steps"].append({"analyze": analysed.status_code})
        if analysed.status_code != 200:
            print("analyze failed", analysed.status_code, analysed.text)
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            return 1
        analysis = analysed.json()["analysis"]
        report["analysis"] = {
            "summary": analysis.get("summary"),
            "features": len(analysis.get("features", [])),
            "ui": len(analysis.get("ui", [])),
            "clarifications": len(analysis.get("clarifications", [])),
            "risks": len(analysis.get("risks", [])),
            "first_feature": (analysis.get("features") or [{}])[0].get("name"),
        }

        planned = client.post(
            f"/api/platform/requirements/{requirement['id']}/plan", json={"create_plan": True}
        )
        report["steps"].append({"plan": planned.status_code})
        if planned.status_code == 200:
            body = planned.json()
            report["plan"] = {
                "person_days": body["plan"].get("person_days"),
                "milestones": len(body["plan"].get("milestones", [])),
                "test_plan": body.get("test_plan"),
            }
        else:
            print("plan failed", planned.status_code, planned.text)

        chatted = client.post(
            f"/api/platform/requirements/{requirement['id']}/chat",
            json={"message": "导出超过 5000 条时后台任务的失败重试策略，需要在分析里的待澄清项补一条。"},
        )
        report["steps"].append({"chat": chatted.status_code})
        if chatted.status_code == 200:
            body = chatted.json()
            report["chat"] = {
                "reply_chars": len(body.get("reply", "")),
                "analysis_updated": body.get("analysis_updated"),
                "messages": len(body["requirement"].get("messages", [])),
                "reply_head": (body.get("reply") or "")[:160],
            }
        else:
            print("chat failed", chatted.status_code, chatted.text)

        final = client.get(f"/api/platform/requirements/{requirement['id']}").json()
        report["final"] = {
            "status": final["status"],
            "has_analysis": bool(final["analysis"]),
            "has_plan": bool(final["plan"]),
            "messages": len(final["messages"]),
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
