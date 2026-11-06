# Phase 0 · 测试记录

> 记录时间：2026-11-06
> 环境：Windows 11 · Python（仓库 `.venv`）· Node.js + Vite · SQLite · FastAPI TestClient / 真实 uvicorn

## 1. 后端单测

命令：

```powershell
cd E:\ailearning\ai-qa-lab
.venv\Scripts\python.exe -m pytest apps/sut/backend/tests/test_skills_registry.py -q
```

结果：`8 passed, 1 warning in 1.25s`

覆盖用例：

| 用例 | 断言点 | 结果 |
| --- | --- | --- |
| `test_list_skills_returns_builtins` | 至少含 `case.generate / case.list / project.list`，字段齐全 | PASS |
| `test_list_skills_filters_by_category` | `?category=case` 只返回 case | PASS |
| `test_get_skill_descriptor` | 单个描述含 `requirement` 输入字段 | PASS |
| `test_get_missing_skill_returns_404` | 未知 id → 404 | PASS |
| `test_run_unknown_skill_returns_404` | 运行未知 skill → 404 | PASS |
| `test_run_project_list_skill` | 返回 `projects` + `total` | PASS |
| `test_run_case_list_skill_filters_by_project` | 按项目过滤命中 1 条 | PASS |
| `test_run_case_generate_requires_requirement` | 缺 requirement → 400 | PASS |

## 2. 全量回归

命令：

```powershell
.venv\Scripts\python.exe -m pytest apps/sut/backend/tests -q
```

结果：`72 passed, 1 warning in 2.40s`（原有 64 条 + 新增 8 条，全部通过）

## 3. 接口冒烟（真实 uvicorn）

启动：

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000
```

| 请求 | 结果 |
| --- | --- |
| `GET /health` | `200 {"status":"ok","service":"sut","version":"1.1.0"}` |
| `GET /api/platform/skills` | `200`，返回 `case.generate, case.list, project.list` |
| `POST /api/platform/skills/project.list/run` | `200 {"ok":true,...,"total":0}`（空库时） |
| `GET /ui/` | `200`，534 B（SPA 入口） |

## 4. AI 生成端到端（skill 链路）

前置：在 `系统 AI 配置` 注册模型（DeepSeek / `deepseek-chat`），服务进程带 `DEEPSEEK_API_KEY`。

```powershell
POST /api/platform/skills/case.generate/run
{"project_id":1,"requirement":"登录页需要支持手机号+密码登录；错误密码提示；连续5次失败锁定30分钟","max_cases":5}
```

结果：`200`，生成 5 条 draft 用例（id 6–10：正确登录 / 密码错误提示 / 5 次失败锁定 / 手机号为空 / 手机号格式非法），`model_name=deepseek-chat`，`prompt_version=case-gen-v1`。

> 说明：PowerShell 控制台按 GBK 解码 UTF-8，输出中文显示为乱码；数据库与浏览器端中文正常（见 `docs/screenshots/phase0-functional.png`）。

## 5. 前端构建

```powershell
cd apps/sut/frontend
npm install
npm run build
```

结果：`✓ built in 7.14s`，新增 chunk 均正常产出（`ProjectsView / ProjectOverview / SystemAiView / AiLogsView / FunctionalView / ModulePlaceholder` 等）。仅剩 rollup 的 chunk > 500 kB 提示（既有问题，与本阶段无关）。

## 6. 视觉回归（Playwright）

脚本：`scripts/phase0_visual_check.py`

| 页面 | 截图 | 结果 |
| --- | --- | --- |
| `/` | `docs/screenshots/phase0-overview.png` | 5 组侧栏 + 概览 6 卡 + skills 表 |
| `/projects` | `phase0-projects.png` | 列表 + 新建表单 |
| `/system-ai` | `phase0-system-ai.png` | 三 Tab，大模型列表 |
| `/functional` | `phase0-functional.png` | 生成表单 + 用例列表 + skill 说明 |
| `/requirements` | `phase0-requirements.png` | 占位页（Phase 1） |
| `/api-automation` | `phase0-api-automation.png` | 占位页（Phase 3） |

附带产出 `docs/screenshots/phase0-sidebar.txt`（侧栏纯文本快照），确认 13 项菜单 + 开发工具折叠组全部渲染。

## 7. 已知问题

1. `case.generate` 依赖服务进程环境变量 `DEEPSEEK_API_KEY`；`.env` 不会自动注入 uvicorn（当前启动脚本手动加载）。Phase 1 会在 `settings` 启动时统一 `load_dotenv`。
2. 功能测试页用例表在 1440px 下「优先级 / 状态」两列被挤压，Phase 2 收紧列宽并加状态筛选。
3. 占位页只声明能力，没有真实交互；按 Phase 1–5 逐项替换。
