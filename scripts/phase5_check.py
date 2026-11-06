"""Phase 5 sanity checks: manual case, execution, script export, AI explore, chat."""

from __future__ import annotations

import json

import httpx

BASE = "http://127.0.0.1:8000/api/platform"
UI = "http://127.0.0.1:8000"


def main() -> int:
    client = httpx.Client(timeout=240)

    created = client.post(
        f"{BASE}/ui-cases",
        json={
            "project_id": 2,
            "title": "手工用例：打开项目管理页并校验标题",
            "module": "UI 冒烟",
            "base_url": UI,
            "env": {},
            "steps": [
                {"action": "goto", "value": f"{UI}/ui/#/projects"},
                {"action": "wait", "ms": 800},
                {"action": "assert_text", "target": "body", "value": "项目管理"},
                {"action": "assert_url", "value": "/projects"},
            ],
            "status": "ready",
        },
    )
    print("create", created.status_code)
    case = created.json()
    print("case id", case["id"], "steps", len(case["steps"]))

    run = client.post(f"{BASE}/ui-cases/{case['id']}/run")
    print("run", run.status_code)
    data = run.json()
    print("status", data.get("status"), "ms", data.get("duration_ms"))
    print("steps", [(s["action"], s["ok"]) for s in data.get("steps", [])])
    print("error", data.get("error"))

    script = client.get(f"{BASE}/ui-cases/{case['id']}/script").json()
    print("script lines", len(script["script"].splitlines()))
    print(script["script"][:240].replace("\n", " | "))

    bad = client.post(f"{BASE}/ui-cases/999999/run")
    print("missing case ->", bad.status_code)

    print("--- AI explore ---")
    explore = client.post(
        f"{BASE}/ui-explore",
        json={
            "project_id": 2,
            "url": f"{UI}/ui/#/knowledge-base",
            "goal": "打开知识库页面，确认页面上有「试检索」入口",
            "save": True,
        },
    )
    print("explore", explore.status_code)
    if explore.status_code == 200:
        info = explore.json()
        print("title", info.get("title"), "nodes", info.get("nodes"))
        print("reasoning", (info.get("reasoning") or "")[:120])
        print("steps", json.dumps(info.get("steps"), ensure_ascii=False)[:400])
        print("saved case", (info.get("case") or {}).get("id"))
    else:
        print(explore.text[:300])

    print("--- AI chat ---")
    chat = client.post(
        f"{BASE}/ui-chat",
        json={"url": f"{UI}/ui/#/knowledge-base", "question": "这个页面上有哪些主要功能区域？"},
    )
    print("chat", chat.status_code)
    print((chat.json().get("reply") if chat.status_code == 200 else chat.text)[:300])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
