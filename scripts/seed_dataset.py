"""Build a complete, testable dataset on a running platform.

Every project is topped up to >= 10 items in each dimension, then a set of
real executions is run and recorded. Safe to re-run: it tops up by title.

Usage:
    python scripts/seed_dataset.py --base http://127.0.0.1:8000 --ai --ui-run
    python scripts/seed_dataset.py --base https://ai-qa-lab-production.up.railway.app
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "dataset"

THEMES = [
    ("电商后台", "shop", "商品、订单、履约与售后的中台"),
    ("内容社区", "community", "内容发布、审核与互动"),
    ("在线教育", "edu", "课程、学习进度与考试"),
    ("物流调度", "logistics", "运单、网点与骑手调度"),
    ("医疗预约", "clinic", "挂号、排班与就诊记录"),
    ("金融风控", "risk", "授信、反欺诈与额度"),
    ("招聘平台", "hr", "职位、投递与面试"),
    ("SaaS 计费", "billing", "套餐、账单与发票"),
    ("IoT 设备", "iot", "设备注册、遥测与告警"),
    ("旅行预订", "travel", "酒店、机票与行程"),
    ("客服工单", "ticket", "工单流转、SLA 与满意度"),
    ("数据分析", "bi", "指标、报表与权限"),
]

FEATURES = [
    ("登录鉴权", "账号密码登录、Token 校验与过期处理"),
    ("订单管理", "下单、取消、状态流转与列表筛选"),
    ("支付退款", "支付回调、部分退款与对账"),
    ("搜索筛选", "关键词搜索、多条件组合与排序"),
    ("批量导出", "CSV 导出、大数据量异步任务"),
    ("权限控制", "角色、数据范围与越权拦截"),
    ("消息通知", "站内信、邮件与失败重试"),
    ("审计日志", "关键操作留痕与检索"),
    ("分页性能", "深分页、索引与响应时间"),
    ("数据看板", "指标口径、环比与权限过滤"),
]

CASE_KINDS = [
    ("{f0}：正确凭证登录返回 200 并下发 Token", "high"),
    ("{f0}：错误密码连续 5 次锁定账号", "high"),
    ("{f1}：创建成功后列表可见且状态为待处理", "high"),
    ("{f1}：取消后再次取消返回业务错误", "medium"),
    ("{f2}：部分退款金额超过原额被拒绝", "high"),
    ("{f3}：多条件组合筛选结果与预期一致", "medium"),
    ("{f4}：超过 5000 条导出转异步任务", "medium"),
    ("{f5}：普通角色访问管理接口返回 403", "high"),
    ("{f7}：审计日志可按操作人检索", "low"),
    ("{f9}：看板指标与明细数据对得上", "medium"),
]

# Executable steps: the plan executor sends these against the platform itself.
# Two of them expect a status the platform does not return, so a real run has
# both passes and failures (which is what a realistic dataset looks like).
CASE_STEPS = [
    ("GET", "/api/platform/summary", 200),
    ("GET", "/api/platform/projects", 200),
    ("GET", "/api/platform/skills", 200),
    ("GET", "/api/platform/models", 200),
    ("GET", "/api/platform/requirements", 200),
    ("GET", "/api/platform/cases", 200),
    ("GET", "/api/platform/knowledge-bases", 200),
    ("GET", "/api/platform/api-endpoints", 200),
    ("GET", "/api/platform/ui-cases", 200),
    ("GET", "/api/platform/summary", 201),
]

UI_FLOWS = [
    ("打开项目概览并确认统计卡片可见", "#/overview", "项目概览"),
    ("打卡项目管理页并确认列表渲染", "#/projects", "项目管理"),
    ("进入需求管理并确认筛选栏存在", "#/requirements", "需求管理"),
    ("进入功能测试并切换到用例管理", "#/functional", "功能测试"),
    ("进入知识库并确认文档列表", "#/kb", "知识库"),
    ("进入接口自动化并确认表格渲染", "#/api-automation", "接口自动化"),
    ("进入 UI 自动化并确认三个页签", "#/ui-automation", "UI 自动化"),
    ("进入环境管理并确认新建表单", "#/environments", "环境管理"),
    ("进入模块管理并确认项目下拉", "#/modules", "模块管理"),
    ("进入成员管理并确认角色列", "#/members", "成员管理"),
]


class Api:
    def __init__(self, base: str, key: str = "") -> None:
        self.base = base.rstrip("/")
        headers = {"X-API-Key": key} if key else {}
        self.client = httpx.Client(base_url=self.base, timeout=180.0, headers=headers)

    def request(self, method: str, path: str, **kwargs):
        for attempt in range(3):
            try:
                response = self.client.request(method, path, **kwargs)
            except httpx.HTTPError:
                if attempt == 2:
                    raise
                time.sleep(1.5)
                continue
            if response.status_code >= 400:
                raise RuntimeError(f"{method} {path} -> {response.status_code} {response.text[:300]}")
            if response.status_code == 204 or not response.content:
                return None
            return response.json()
        return None

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, **kw):
        return self.request("POST", path, **kw)

    def patch(self, path, **kw):
        return self.request("PATCH", path, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)


def platform_spec(slug: str, theme: str, base_url: str) -> dict:
    """A spec that mixes real, executable platform endpoints with synthetic ones."""
    paths = {
        "/api/platform/summary": ("get", "平台概览统计"),
        "/api/platform/projects": ("get", "项目列表"),
        "/api/platform/skills": ("get", "能力清单"),
        "/api/platform/models": ("get", "模型配置列表"),
        f"/api/{slug}/orders": ("get", f"{theme}订单列表"),
        f"/api/{slug}/orders/{{order_id}}": ("get", f"{theme}订单详情"),
        f"/api/{slug}/export": ("post", f"{theme}批量导出"),
        f"/api/{slug}/users/{{user_id}}/roles": ("patch", f"{theme}角色调整"),
        f"/api/{slug}/metrics": ("get", f"{theme}看板指标"),
        f"/api/{slug}/audit-logs": ("get", f"{theme}审计日志"),
    }
    return {
        "openapi": "3.0.3",
        "info": {"title": f"{theme} 接口清单", "version": "1.0.0"},
        "servers": [{"url": base_url}],
        "paths": {
            path: {
                method: {
                    "tags": [f"{theme}接口"],
                    "summary": summary,
                    "parameters": [
                        {"name": "page", "in": "query", "schema": {"type": "integer"}},
                        {"name": "status", "in": "query", "schema": {"type": "string"}},
                    ],
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "status": {"type": "string"},
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }
            for path, (method, summary) in paths.items()
        },
    }


def kb_documents(theme: str, feature: str, detail: str) -> list[tuple[str, str]]:
    return [
        (
            f"{theme}-{feature}-接口约定.md",
            f"# {theme} · {feature} 接口约定\n\n"
            f"## 背景\n{theme}的{feature}由业务平台统一提供，{detail}。\n\n"
            "## 约定\n1. 所有写接口需要 Bearer 访问密钥，匿名请求返回 401。\n"
            "2. 列表接口默认 page=1、size=20，最大 size=200。\n"
            "3. 单次导出超过 5000 条时接口返回 202，转后台任务，完成后站内信通知。\n"
            "4. 时间字段统一 ISO8601，时区 Asia/Shanghai。\n\n"
            "## 错误码\n- 400 参数校验失败，body 里带 field\n- 403 角色无权限\n- 409 状态冲突\n",
        ),
        (
            f"{theme}-{feature}-测试要点.md",
            f"# {theme} · {feature} 测试要点\n\n"
            "## 必测场景\n- 正常流：主流程字段完整、状态流转正确\n"
            "- 边界：分页 size=0/1/200/201，导出 4999/5000/5001 条\n"
            "- 异常：非法状态值、越权访问、重复提交\n\n"
            "## 数据准备\n- 至少 1 个普通角色 + 1 个管理员\n"
            "- 造 5001 条数据用于导出阈值验证\n\n"
            "## 判定标准\n接口返回码与业务状态一致，列表与详情数据一致。\n",
        ),
        (
            f"{theme}-回归清单.md",
            "# 回归清单\n\n"
            "| 编号 | 检查项 | 预期 |\n| --- | --- | --- |\n"
            "| R1 | 登录后 Token 有效期 | 2 小时 |\n"
            "| R2 | 列表深分页 page=500 | 响应 < 800ms |\n"
            "| R3 | 导出任务失败重试 | 最多 3 次 |\n"
            "| R4 | 审计日志留存 | 180 天 |\n",
        ),
        (
            f"{theme}-历史缺陷.md",
            "# 历史缺陷复盘\n\n"
            "1. 导出 5001 条未转异步，接口 504 —— 已修复，阈值改为 5000。\n"
            "2. 普通角色可调用管理接口 —— 已补 403 拦截。\n"
            "3. 深分页 page=500 响应 3.2s —— 已加复合索引。\n",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--key", default="")
    parser.add_argument("--ai", action="store_true", help="run real LLM analysis/generation")
    parser.add_argument("--ai-limit", type=int, default=4)
    parser.add_argument("--ui-run", action="store_true", help="execute UI cases with Playwright")
    parser.add_argument("--ui-limit", type=int, default=10)
    parser.add_argument("--skip-plan-run", action="store_true", help="do not execute functional plans")
    parser.add_argument("--label", default="local")
    args = parser.parse_args()

    api = Api(args.base, args.key)
    health = api.get("/health")
    print("health", health, flush=True)

    started = datetime.now()
    stats: dict[str, int] = {}
    tests: list[dict] = []

    def bump(key: str, value: int = 1) -> None:
        stats[key] = stats.get(key, 0) + value

    # 1. projects -----------------------------------------------------------
    existing = {item["name"]: item for item in api.get("/api/platform/projects")}
    projects: list[dict] = list(existing.values())
    for theme, slug, description in THEMES:
        if theme not in existing:
            created = api.post("/api/platform/projects", json={"name": theme, "description": description})
            projects.append(created)
            existing[theme] = created
            bump("projects")
    print(f"projects={len(projects)}", flush=True)

    # 2. global config ------------------------------------------------------
    users = {item["name"] for item in api.get("/api/platform/users")}
    for name, email, role in [
        ("沈乐", "shenle@example.com", "管理员"),
        ("张三", "zhangsan@example.com", "测试"),
        ("李四", "lisi@example.com", "开发"),
        ("王五", "wangwu@example.com", "产品"),
        ("赵六", "zhaoliu@example.com", "访客"),
        ("孙七", "sunqi@example.com", "测试"),
        ("周八", "zhouba@example.com", "开发"),
        ("吴九", "wujiu@example.com", "测试"),
        ("郑十", "zhengshi@example.com", "访客"),
        ("陈一", "chenyi@example.com", "产品"),
    ]:
        if name not in users:
            api.post("/api/platform/users", json={"name": name, "email": email, "role": role, "note": "种子账号"})
            bump("users")

    models = {(item["name"], item.get("kind", "chat")) for item in api.get("/api/platform/models")}
    for name, provider, base, model, kind in [
        ("DeepSeek 主力", "deepseek", "https://api.deepseek.com", "deepseek-chat", "chat"),
        ("DeepSeek 备用", "deepseek", "https://api.deepseek.com", "deepseek-reasoner", "chat"),
        ("通义千问", "qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus", "chat"),
        ("Kimi", "moonshot", "https://api.moonshot.cn/v1", "moonshot-v1-8k", "chat"),
        ("GLM-4", "zhipu", "https://open.bigmodel.cn/api/paas/v4", "glm-4-plus", "chat"),
        ("本地 Ollama", "ollama", "http://127.0.0.1:11434/v1", "qwen2.5:7b", "chat"),
        ("BGE-M3", "siliconflow", "https://api.siliconflow.cn/v1", "BAAI/bge-m3", "embedding"),
        ("text-embedding-3", "openai", "https://api.openai.com/v1", "text-embedding-3-small", "embedding"),
        ("bge-large-zh", "siliconflow", "https://api.siliconflow.cn/v1", "BAAI/bge-large-zh-v1.5", "embedding"),
        ("Midscene 视觉", "openai", "https://api.openai.com/v1", "gpt-4o", "vision"),
        ("Qwen-VL", "dashscope", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-vl-max", "vision"),
        ("GLM-4V", "zhipu", "https://open.bigmodel.cn/api/paas/v4", "glm-4v-plus", "vision"),
    ]:
        if (name, kind) not in models:
            api.post(
                "/api/platform/models",
                json={
                    "name": name,
                    "provider": provider,
                    "base_url": base,
                    "model_name": model,
                    "kind": kind,
                    "enabled": True,
                },
            )
            bump(f"models_{kind}")

    # 3. per-project content ------------------------------------------------
    ai_budget = args.ai_limit
    for index, project in enumerate(projects):
        pid = project["id"]
        name = project["name"]
        theme_entry = next((item for item in THEMES if item[0] == name), None)
        if theme_entry:
            theme, slug, description = theme_entry
        else:
            theme = name
            slug = f"p{pid}"
            description = project.get("description") or f"{name} 的业务系统"
        feats = [f[0] for f in FEATURES]
        details = [f[1] for f in FEATURES]

        # modules
        modules = {item["name"] for item in api.get("/api/platform/modules", params={"project_id": pid})}
        for feature, detail in FEATURES[:4]:
            if feature not in modules:
                api.post(
                    "/api/platform/modules",
                    json={"project_id": pid, "name": feature, "owner": "张三", "description": detail},
                )
                bump("modules")

        # members
        members = {item["name"] for item in api.get("/api/platform/members", params={"project_id": pid})}
        for member, role, email in [
            ("张三", "测试", "zhangsan@example.com"),
            ("李四", "开发", "lisi@example.com"),
            ("王五", "产品", "wangwu@example.com"),
            ("赵六", "运维", "zhaoliu@example.com"),
        ]:
            if member not in members:
                api.post(
                    "/api/platform/members",
                    json={"project_id": pid, "name": member, "role": role, "email": email},
                )
                bump("members")

        # environments
        envs = {item["name"] for item in api.get("/api/platform/environments", params={"project_id": pid})}
        for suffix, kind in [("本地", "dev"), ("测试", "test"), ("预发", "staging"), ("生产", "prod")]:
            env_name = f"{env_name_prefix(theme)}{suffix}"
            if env_name not in envs:
                api.post(
                    "/api/platform/environments",
                    json={
                        "project_id": pid,
                        "name": env_name,
                        "kind": kind,
                        "base_url": f"https://{slug}-{kind}.example.com",
                        "variables": {"token": f"{slug}-{kind}-token", "tenant": slug},
                        "note": f"{theme} {kind} 环境",
                    },
                )
                bump("environments")

        # requirements
        have = api.get("/api/platform/requirements", params={"project_id": pid})
        titles = {item["title"] for item in have}
        for i, feature in enumerate(FEATURES):
            title = f"{theme}：{feature}需求"
            if title in titles:
                continue
            body = (
                f"# {theme} · {feature}\n\n## 背景\n{description}，{feature}目前依赖人工处理，"
                f"效率低且容易出错。\n\n## 需求\n1. {details[i]}\n2. 列表支持按状态筛选与创建时间排序。\n"
                "3. 超过 5000 条导出时提示并转后台任务，完成后站内信通知。\n\n"
                "## 约束\n- 复用现有权限体系\n- 不新增独立部署单元\n"
            )
            created = api.post(
                "/api/platform/requirements",
                json={
                    "project_id": pid,
                    "title": title,
                    "body": body,
                    "status": "draft",
                    "priority": ["high", "medium", "low"][i % 3],
                },
            )
            bump("requirements")
            if args.ai and ai_budget > 0:
                try:
                    api.post(f"/api/platform/requirements/{created['id']}/analyze", json={})
                    api.post(f"/api/platform/requirements/{created['id']}/plan", json={"create_plan": True})
                    tests.append(
                        {
                            "kind": "requirement_ai",
                            "project": name,
                            "requirement": title,
                            "result": "analyzed+planned",
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    tests.append({"kind": "requirement_ai", "project": name, "requirement": title, "result": f"failed: {exc}"})
                ai_budget -= 1

        # functional cases
        cases = api.get("/api/platform/cases", params={"project_id": pid})
        have_titles = {item["title"] for item in cases}
        created_cases: list[int] = []
        for case_index, (template, priority) in enumerate(CASE_KINDS):
            title = template.format(f0=feats[0], f1=feats[1], f2=feats[2], f3=feats[3], f4=feats[4], f5=feats[5], f7=feats[7], f9=feats[9])
            title = f"{theme}-{title}"
            if title in have_titles:
                continue
            method, path, expected_status = CASE_STEPS[case_index % len(CASE_STEPS)]
            steps = [
                {"action": method, "target": path, "data": "", "assert": f"status={expected_status}"},
            ]
            row = api.post(
                "/api/platform/cases",
                json={
                    "project_id": pid,
                    "title": title,
                    "module": "api",
                    "priority": priority,
                    "steps": f"1. {method} {path}\n2. 断言 status={expected_status}",
                    "expected": f"status={expected_status}",
                    "steps_json": json.dumps(steps, ensure_ascii=False),
                },
            )
            created_cases.append(row["id"])
            bump("cases")

        # give the project a realistic status mix
        all_cases = api.get("/api/platform/cases", params={"project_id": pid})
        if all_cases:
            ids = [item["id"] for item in all_cases]
            api.post("/api/platform/cases/batch", json={"ids": ids[: max(1, len(ids) // 3)], "action": "draft"})
            api.post(
                "/api/platform/cases/batch",
                json={"ids": ids[len(ids) // 3 : max(1, 2 * len(ids) // 3)], "action": "submit_review"},
            )
            api.post(
                "/api/platform/cases/batch",
                json={"ids": ids[max(1, 2 * len(ids) // 3) :], "action": "approve"},
            )

        # plans
        plans = api.get("/api/platform/plans", params={"project_id": pid})
        for suffix in ("冒烟", "回归"):
            plan_name = f"{theme} {suffix}计划"
            if plan_name not in {item["name"] for item in plans}:
                api.post("/api/platform/plans", json={"project_id": pid, "name": plan_name})
                bump("plans")

        # one real plan execution per project (functional cases against the platform)
        if not args.skip_plan_run:
            plans = api.get("/api/platform/plans", params={"project_id": pid})
            smoke = next((item for item in plans if item["name"] == f"{theme} 冒烟计划"), None)
            approved = [item["id"] for item in api.get("/api/platform/cases", params={"project_id": pid}) if item["status"] == "approved"][:6]
            if smoke and approved:
                try:
                    api.post(
                        f"/api/platform/plans/{smoke['id']}/execute",
                        json={"case_ids": approved, "base_url": args.base},
                    )
                    execution = None
                    for _ in range(14):
                        time.sleep(1.5)
                        rows = api.get("/api/platform/executions", params={"limit": 200})
                        candidates = [row for row in rows if row["plan_id"] == smoke["id"]]
                        if candidates:
                            latest = max(candidates, key=lambda row: row["id"])
                            if latest["status"] != "running":
                                execution = latest
                                break
                    if execution:
                        tests.append(
                            {
                                "kind": "plan_execution",
                                "project": name,
                                "plan": smoke["name"],
                                "status": execution["status"],
                                "total": execution["total"],
                                "passed": execution["passed"],
                                "failed": execution["failed"],
                                "duration_ms": execution.get("duration_ms"),
                            }
                        )
                        bump("executions")
                    else:
                        tests.append({"kind": "plan_execution", "project": name, "plan": smoke["name"], "status": "timeout"})
                except Exception as exc:  # noqa: BLE001
                    tests.append(
                        {"kind": "plan_execution", "project": name, "plan": smoke["name"], "status": f"error: {exc}"}
                    )

        # knowledge bases
        kbs = api.get("/api/platform/knowledge-bases", params={"project_id": pid})
        kb_names = {item["name"] for item in kbs}
        for kb_name, chunk, overlap in [
            (f"{theme}接口知识库", 600, 100),
            (f"{theme}测试规范库", 400, 60),
        ]:
            kb = next((item for item in kbs if item["name"] == kb_name), None)
            if kb is None:
                kb = api.post(
                    "/api/platform/knowledge-bases",
                    json={
                        "project_id": pid,
                        "name": kb_name,
                        "description": f"{theme}的接口约定与测试规范",
                        "chunk_size": chunk,
                        "chunk_overlap": overlap,
                    },
                )
                bump("knowledge_bases")
            docs = api.get(f"/api/platform/knowledge-bases/{kb['id']}/documents")
            have_docs = {item["filename"] for item in docs}
            for doc_index, feature in enumerate(feats[:5]):
                for filename, text in kb_documents(theme, feature, details[doc_index]):
                    if filename in have_docs:
                        continue
                    api.post(
                        f"/api/platform/knowledge-bases/{kb['id']}/documents/text",
                        json={"filename": filename, "text": text},
                    )
                    bump("knowledge_documents")

        # api assets + endpoints
        assets = api.get("/api/platform/api-assets", params={"project_id": pid})
        if not any(item["name"] == f"{theme} 接口清单" for item in assets):
            api.post(
                "/api/platform/api-assets/import",
                json={
                    "project_id": pid,
                    "name": f"{theme} 接口清单",
                    "spec": json.dumps(platform_spec(slug, theme, args.base), ensure_ascii=False),
                },
            )
            bump("api_assets")

        endpoints = api.get("/api/platform/api-endpoints", params={"project_id": pid})
        real = [item for item in endpoints if item["path"].startswith("/api/platform/")]
        synthetic = [item for item in endpoints if not item["path"].startswith("/api/platform/")]

        api_cases = api.get("/api/platform/api-cases", params={"project_id": pid})
        api_titles = {item["title"] for item in api_cases}
        for endpoint in real:
            title = f"{theme}-{endpoint['method']} {endpoint['path']} 返回 200"
            if title in api_titles:
                continue
            api.post(
                "/api/platform/api-cases",
                json={
                    "project_id": pid,
                    "endpoint_id": endpoint["id"],
                    "kind": "case",
                    "title": title,
                    "module": endpoint["module"],
                    "status": "approved",
                    "expected": "status=200",
                    "steps": [
                        {
                            "name": "直连调用",
                            "method": endpoint["method"],
                            "url": endpoint["path"],
                            "headers": {},
                            "params": {},
                            "body": None,
                            "expect": {"status": 200},
                        }
                    ],
                },
            )
            bump("api_cases")

        for endpoint in synthetic[:6]:
            title = f"{theme}-{endpoint['method']} {endpoint['path']} 参数校验"
            if title in api_titles:
                continue
            api.post(
                "/api/platform/api-cases",
                json={
                    "project_id": pid,
                    "endpoint_id": endpoint["id"],
                    "kind": "case",
                    "title": title,
                    "module": endpoint["module"],
                    "status": "draft",
                    "expected": "status=400",
                    "steps": [
                        {
                            "name": "非法分页",
                            "method": endpoint["method"],
                            "url": endpoint["path"],
                            "params": {"page": "abc"},
                            "expect": {"status": 400},
                        }
                    ],
                },
            )
            bump("api_cases_draft")

        scenarios = [item for item in api_cases if item["kind"] == "scenario"]
        if len(scenarios) < 2:
            api.post(
                "/api/platform/api-cases",
                json={
                    "project_id": pid,
                    "kind": "scenario",
                    "title": f"{theme}-创建项目后分页查询校验数据一致",
                    "module": "项目管理",
                    "status": "approved",
                    "expected": "两步均 200",
                    "steps": [
                        {
                            "name": "分页查询项目",
                            "method": "GET",
                            "url": "/api/platform/projects",
                            "params": {"page": 1},
                            "extract": {"first_project": "0.name"},
                            "expect": {"status": 200},
                        },
                        {
                            "name": "查概览",
                            "method": "GET",
                            "url": "/api/platform/summary",
                            "expect": {"status": 200},
                        },
                    ],
                },
            )
            bump("api_scenarios")

        # ui cases
        ui_cases = api.get("/api/platform/ui-cases", params={"project_id": pid})
        ui_titles = {item["title"] for item in ui_cases}
        for flow, route, heading in UI_FLOWS:
            title = f"{theme}-{flow}"
            if title in ui_titles:
                continue
            api.post(
                "/api/platform/ui-cases",
                json={
                    "project_id": pid,
                    "title": title,
                    "module": "页面巡检",
                    "base_url": args.base,
                    "env": {},
                    "status": "ready",
                    "steps": [
                        {"action": "goto", "value": f"{args.base}/ui/{route}"},
                        {"action": "assert_text", "target": "body", "value": heading},
                    ],
                },
            )
            bump("ui_cases")

        # defects
        defects = api.get("/api/platform/defects", params={"project_id": pid})
        defect_titles = {item["title"] for item in defects}
        for title, severity in [
            (f"{theme}-导出超过 5000 条返回 504", "high"),
            (f"{theme}-普通角色可访问管理接口", "critical"),
            (f"{theme}-深分页响应超过 3s", "medium"),
        ]:
            if title not in defect_titles:
                api.post(
                    "/api/platform/defects",
                    json={"project_id": pid, "title": title, "severity": severity, "status": "open"},
                )
                bump("defects")

        print(f"project {pid} {name} done", flush=True)

    # 4. run real tests -----------------------------------------------------
    for project in projects:
        pid = project["id"]
        name = project["name"]

        api_cases = api.get("/api/platform/api-cases", params={"project_id": pid})
        runnable = [item for item in api_cases if item["status"] == "approved"][:3]
        for case in runnable:
            try:
                run = api.post(f"/api/platform/api-cases/{case['id']}/run", params={"base_url": args.base})
                tests.append(
                    {
                        "kind": "api_case_run",
                        "project": name,
                        "case": case["title"],
                        "status": run.get("status"),
                        "status_code": run.get("status_code"),
                        "duration_ms": run.get("duration_ms"),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                tests.append({"kind": "api_case_run", "project": name, "case": case["title"], "status": f"error: {exc}"})
            bump("runs_api")

        scenarios = [item for item in api_cases if item["kind"] == "scenario"][:1]
        for case in scenarios:
            try:
                run = api.post(f"/api/platform/api-cases/{case['id']}/run", params={"base_url": args.base})
                tests.append(
                    {
                        "kind": "api_scenario_run",
                        "project": name,
                        "case": case["title"],
                        "status": run.get("status"),
                        "steps": len(run.get("steps") or []),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                tests.append({"kind": "api_scenario_run", "project": name, "case": case["title"], "status": f"error: {exc}"})
            bump("runs_api")

        kbs = api.get("/api/platform/knowledge-bases", params={"project_id": pid})
        for kb in kbs[:1]:
            for query in ("导出超过 5000 条怎么处理", "普通角色访问管理接口", "深分页响应慢"):
                try:
                    hit = api.post(f"/api/platform/knowledge-bases/{kb['id']}/search", json={"query": query, "top_k": 3})
                    tests.append(
                        {
                            "kind": "kb_search",
                            "project": name,
                            "kb": kb["name"],
                            "query": query,
                            "hits": len(hit["hits"]),
                            "took_ms": hit["took_ms"],
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    tests.append({"kind": "kb_search", "project": name, "query": query, "status": f"error: {exc}"})
                bump("searches")

    if args.ui_run:
        budget = args.ui_limit
        for project in projects:
            if budget <= 0:
                break
            ui_cases = api.get("/api/platform/ui-cases", params={"project_id": project["id"]})
            for case in ui_cases[:2]:
                if budget <= 0:
                    break
                try:
                    run = api.post(f"/api/platform/ui-cases/{case['id']}/run")
                    tests.append(
                        {
                            "kind": "ui_case_run",
                            "project": project["name"],
                            "case": case["title"],
                            "status": run.get("status"),
                            "duration_ms": run.get("duration_ms"),
                            "steps": len(run.get("steps") or []),
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    tests.append(
                        {"kind": "ui_case_run", "project": project["name"], "case": case["title"], "status": f"error: {exc}"}
                    )
                budget -= 1
                bump("runs_ui")

    # 5. summary ------------------------------------------------------------
    summary = api.get("/api/platform/summary")
    skills = api.get("/api/platform/skills")
    finished = datetime.now()
    payload = {
        "label": args.label,
        "base": args.base,
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": finished.isoformat(timespec="seconds"),
        "elapsed_seconds": round((finished - started).total_seconds(), 1),
        "created": stats,
        "platform_summary": summary,
        "skills": len(skills),
        "tests": tests,
        "counts": {
            "projects": len(projects),
            "requirements": len(api.get("/api/platform/requirements", params={"limit": 500})),
            "cases": len(api.get("/api/platform/cases", params={"limit": 500})),
            "knowledge_bases": len(api.get("/api/platform/knowledge-bases", params={"limit": 200})),
            "knowledge_documents": sum(
                len(api.get(f"/api/platform/knowledge-bases/{kb['id']}/documents", params={"limit": 200}))
                for kb in api.get("/api/platform/knowledge-bases", params={"limit": 200})
            ),
            "api_assets": len(api.get("/api/platform/api-assets")),
            "api_endpoints": len(api.get("/api/platform/api-endpoints", params={"limit": 1000})),
            "api_cases": len(api.get("/api/platform/api-cases", params={"limit": 1000})),
            "api_runs": len(api.get("/api/platform/api-runs", params={"limit": 200})),
            "ui_cases": len(api.get("/api/platform/ui-cases", params={"limit": 200})),
            "ui_runs": len(api.get("/api/platform/ui-runs", params={"limit": 200})),
            "environments": sum(
                len(api.get("/api/platform/environments", params={"project_id": item["id"]})) for item in projects
            ),
            "modules": sum(len(api.get("/api/platform/modules", params={"project_id": item["id"]})) for item in projects),
            "members": sum(len(api.get("/api/platform/members", params={"project_id": item["id"]})) for item in projects),
            "users": len(api.get("/api/platform/users")),
            "models": len(api.get("/api/platform/models")),
            "defects": len(api.get("/api/platform/defects", params={"limit": 500})),
            "plans": len(api.get("/api/platform/plans", params={"limit": 500})),
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / f"{args.label}-{started.strftime('%Y%m%d-%H%M')}.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["counts"], ensure_ascii=False, indent=2))
    print("written", out_file)
    return 0


def env_name_prefix(theme: str) -> str:
    return f"{theme}-"


if __name__ == "__main__":
    sys.exit(main())
