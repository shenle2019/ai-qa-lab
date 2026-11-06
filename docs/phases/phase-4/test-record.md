# Phase 4 · 测试记录

## 环境

- 机器：Windows，仓库 `E:\ailearning\ai-qa-lab`
- Python：`.venv`（httpx 0.28.1、PyYAML 6.0.3、pytest 8.x）
- 服务：`python -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000`
- 数据库：SQLite `sut.db`（`ensure_columns` 补齐 `api_runs.steps_json`）
- 模型：`DeepSeek Default` / `deepseek-chat`，key 来自 `.env`

## 单元与接口测试

```
.venv\Scripts\python.exe -m pytest apps/sut/backend/tests -q
118 passed, 1 warning in 8.68s
```

新增 `apps/sut/backend/tests/test_api_automation.py`，17 条，全部通过：

| 用例 | 覆盖点 |
| --- | --- |
| test_import_openapi_json | JSON 文档导入 3 个接口，字段/方法/模块正确 |
| test_import_openapi_yaml | YAML 文档导入 |
| test_import_rejects_garbage | 非 OpenAPI 文本返回 400 |
| test_endpoint_crud_and_modules | 新建/改/删接口，`/modules` 聚合正确 |
| test_invalid_method_rejected | 非法 HTTP 方法返回 400 |
| test_debug_endpoint_records_run | 调试成功并落一条 kind=debug 记录 |
| test_debug_failure_is_recorded | 调试失败也落库，带错误信息 |
| test_single_case_pass | 单接口用例执行通过 |
| test_case_run_uses_asset_base_url | 不传 base_url 时回退到资产地址 |
| test_scenario_data_flow | 场景两步，`data.id` → `{{ticket_id}}` 数据流 |
| test_scenario_stops_at_failure | 第 2 步失败即停，共 2 条步骤记录 |
| test_case_validation | 缺 steps / 非法 kind 返回 400 |
| test_generate_cases_with_fake_model | 假模型驱动单接口生成，写入 draft |
| test_generate_scenario_with_fake_model | 假模型驱动场景生成，kind=scenario |
| test_diagnose_rejects_passed_run | 成功的执行记录不给归因（400） |
| test_diagnose_failed_run_with_fake_model | 假模型归因写回 `ai_root_cause` |
| test_delete_endpoint_cascades_cases | 删接口连带删用例 |

测试里起了一个真的 `ThreadingHTTPServer`（`/api/tickets` GET/POST/DELETE）当被测系统，断言的
都是真实 HTTP 往返，不是 mock 掉执行器。

## 真实链路冒烟

`scripts/phase4_seed.py`（httpx 直连，结果写 `docs/phases/phase-4/seed-output.json`）：

| 步骤 | 结果 |
| --- | --- |
| 导入自建 spec（4 个真实接口） | 资产 id 1，接口 4 个 |
| 调试 `GET /api/platform/summary` | passed，200 |
| 单接口 Agent 生成 4 条用例 | 全部 draft，模型 deepseek-chat |
| 执行「正常查询项目列表-默认参数」 | passed |
| 场景 Agent 生成 2 步场景 | `创建项目并查询详情验证名称一致` |
| 执行场景 | passed，`project_id=3` 从第一步流到第二步 |
| 执行「未登录」「非法参数」用例 | failed（期望 401/400，实际 200） |
| AI 归因失败记录 | 输出「问题在服务端，接口未对非法参数类型做校验」，并给修复建议 |

脚本可重复执行：资产/用例已存在时跳过生成，场景会先清掉同名项目保证 201 可复现。

## 视觉验证

`scripts/phase4_visual_check.py` + `scripts/phase4_run_detail.py`（playwright，1440 宽）：

| 截图 | 内容 |
| --- | --- |
| `phase4-api-endpoints.png` | 接口管理：4 个接口，方法彩色标签，用例数，操作列 |
| `phase4-api-assets.png` | 接口资产：版本 3.0.0、Base URL、接口数 |
| `phase4-api-single-agent.png` | 单接口 Agent 表单 |
| `phase4-api-scenario-agent.png` | 场景 Agent 多选接口 |
| `phase4-api-cases.png` | 单接口用例：4 条 AI 生成用例，步骤预览 |
| `phase4-api-scenarios.png` | 接口场景列表 |
| `phase4-api-runs.png` | 执行记录：通过/失败徽章、状态码、耗时 |
| `phase4-api-run-detail.png` | 失败详情：2 步链路 + 请求响应 + AI 归因正文 |
| `phase4-api-debug.png` | 调试抽屉：Base URL、Headers/Query/body |

## 本轮修的问题

| # | 现象 | 原因 | 处理 |
| --- | --- | --- | --- |
| 1 | 场景执行报「接口是相对路径，且没有配置 Base URL」 | 场景不绑定单个接口，资产回退链断在 `resolve_base_url` | 加 `project_base_url()`，执行时三级回退 |
| 2 | 变量没抓到时 URL 变成 `/projects/`，返回 307 | `render` 把缺失变量渲染成空串 | 加 `strict=True`，缺失直接报「变量 {{x}} 没有解析到值」 |
| 3 | 详情抽屉把整段步骤当请求、当响应 | `request_json` 存的是步骤数组，`response_json` 存的是 `{variables, steps}` | 新增 `api_runs.steps_json`，`request/response` 存当步，`steps` 单独存 |
| 4 | 打开详情看不到步骤 | 前端读 `run.steps`，后端没返回 | `serialise_run` 解析 `steps_json`，并补 `variables` 汇总 |
| 5 | 改完序列化后 `test_scenario_data_flow` 失败 | 断言取 `response.variables` | 断言改为顶层 `variables`，语义更直白 |
| 6 | 接口管理工具条每个控件占一整行 | 全局 `select`/`input` 是 `width:100%` | scoped 里 `.toolbar select{width:auto}`、搜索框 `flex:1 1 240px` |
| 7 | 每次进页面都回到没数据的项目 | 项目选择没记忆 | localStorage 记 `aiqa.api.project` |
| 8 | 截图脚本点完「AI 归因」后点不动下一个页签 | 抽屉是 `.modal-mask` 遮罩，没关掉 | 脚本先点「关闭」再继续 |

## 复现命令

```powershell
cd E:\ailearning\ai-qa-lab
.venv\Scripts\python.exe -m pytest apps/sut/backend/tests -q
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000
.venv\Scripts\python.exe scripts\phase4_seed.py
python scripts\phase4_visual_check.py
python scripts\phase4_run_detail.py
```
