"""Seed demo modules/members/embedding/vision rows for Phase 5 screenshots."""

from __future__ import annotations

import httpx

BASE = "http://127.0.0.1:8000/api/platform"
PROJECT = 2

MODULES = [
    ("工单中心", "张三", "工单的创建、流转、导出"),
    ("权限与登录", "李四", "登录、鉴权、角色权限"),
    ("报表与统计", "王五", "汇总看板与导出报表"),
]

MEMBERS = [
    ("张三", "测试", "zhangsan@example.com"),
    ("李四", "开发", "lisi@example.com"),
    ("王五", "产品", "wangwu@example.com"),
]

MODELS = [
    {
        "name": "BGE-M3（备用）",
        "kind": "embedding",
        "provider": "siliconflow",
        "base_url": "https://api.siliconflow.cn/v1",
        "model_name": "BAAI/bge-m3",
    },
    {
        "name": "Midscene 视觉模型",
        "kind": "vision",
        "provider": "openai",
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-4o",
    },
]


def main() -> int:
    client = httpx.Client(timeout=30)
    for name, owner, description in MODULES:
        response = client.post(
            f"{BASE}/modules",
            json={"project_id": PROJECT, "name": name, "owner": owner, "description": description},
        )
        print("module", name, response.status_code)

    for name, role, email in MEMBERS:
        response = client.post(
            f"{BASE}/members",
            json={"project_id": PROJECT, "name": name, "role": role, "email": email},
        )
        print("member", name, response.status_code)

    for payload in MODELS:
        response = client.post(f"{BASE}/models", json=payload)
        print("model", payload["name"], response.status_code)

    print("modules", len(client.get(f"{BASE}/modules", params={"project_id": PROJECT}).json()))
    print("members", len(client.get(f"{BASE}/members", params={"project_id": PROJECT}).json()))
    print("embedding", len(client.get(f"{BASE}/models", params={"kind": "embedding"}).json()))
    print("vision", len(client.get(f"{BASE}/models", params={"kind": "vision"}).json()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
