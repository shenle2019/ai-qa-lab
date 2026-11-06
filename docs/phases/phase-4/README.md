# Phase 4 · 接口自动化

对齐目标站「自动化 → 接口自动化」的七个页签：场景 Agent / 单接口 Agent / 接口资产 / 接口管理 / 单接口用例 / 接口场景 / 执行记录。

## 交付清单

| 能力 | 状态 | 说明 |
| --- | --- | --- |
| OpenAPI 导入 | 完成 | JSON 与 YAML 都能解析，支持 `$ref`、path/operation 参数合并、Swagger2 body |
| 接口管理 | 完成 | 列表、搜索、方法/模块筛选、增删改，按项目隔离 |
| 在线调试 | 完成 | 真发请求，可改 Base URL / Headers / Query / body / 期望状态码，结果落执行记录 |
| 单接口 Agent | 完成 | 选一个接口生成可直接执行的用例，可挂知识库补充接口约定 |
| 场景 Agent | 完成 | 勾多个接口 + 业务目标，生成带 `{{变量}}` 数据流的串联场景 |
| 用例执行 | 完成 | 顺序执行、逐步断言、失败即停、变量在步骤间流转 |
| 执行记录 | 完成 | 调试/用例/场景统一落库，可看逐步请求响应 |
| AI 归因 | 完成 | 失败记录交给大模型定位「断言错 / 用例错 / 服务端缺陷」，结果缓存 |

## 数据模型

```
api_assets      id, project_id, name, source, spec_version, base_url, endpoint_count
api_endpoints   id, project_id, asset_id, method, path, name, module, summary,
                params_json, body_json, responses_json, source
api_cases       id, project_id, endpoint_id, kind(case|scenario), title, module,
                steps_json, expected, status, source, prompt_version
api_runs        id, project_id, case_id, endpoint_id, kind(debug|case|scenario),
                title, status, status_code, duration_ms,
                request_json, response_json, steps_json, error, ai_root_cause
```

`steps_json` 是步骤数组，单接口用例一步，场景多步。每一步长这样：

```json
{
  "name": "创建项目",
  "method": "POST",
  "url": "/api/platform/projects",
  "headers": {"Content-Type": "application/json"},
  "params": {},
  "body": {"name": "自动化测试项目"},
  "extract": {"project_id": "id"},
  "expect": {"status": 201}
}
```

## 执行引擎

`api_runner.py` 负责单步：

1. `render(value, ctx, strict=True)` 把 `{{变量}}` 换成上一步抓到的值；变量缺失直接抛
   `RunError("变量 {{x}} 没有解析到值，请检查上一步的 extract")`，不会悄悄拼出空路径。
2. `_absolute(url, base_url)` 拼绝对地址；相对路径且没有 base_url 时抛「接口是相对路径，且没有配置 Base URL」。
3. `send()` 用 httpx 真发，`follow_redirects=False`（避免 307 掩盖问题），响应体截断 20000 字符。
4. `check_expectation()` 支持三种断言：`status`（int 或数组）、`contains`、`json_path` + `equals`。
5. `extract` 支持 `$.a.b`、`a.0.b`、`header:Location`，抓到的值写回上下文供后续步骤使用。

`api_executor.py` 负责用例级：顺序跑、失败即停、把整次执行（含每步请求响应）写入 `api_runs`。

Base URL 三级回退：调用方显式传入 → 接口所属资产的 `base_url` → 项目最新资产的 `base_url`。

## Skill 契约

| skill id | 分类 | 输入 | 输出 |
| --- | --- | --- | --- |
| `api.case.generate` | api | `endpoint_id`、`count`(1-15)、`kb_id?`、`model_id?` | `{count, used_knowledge, cases[]}`，写库为 draft |
| `api.scenario.generate` | api | `project_id`、`endpoint_ids`(1-12)、`goal`、`model_id?` | `{id, title, steps[]}`，写库 kind=scenario |
| `api.run` | api | `case_id`、`base_url?` | 执行记录 |
| `api.diagnose` | api | `run_id` | `{run_id, ai_root_cause}` |

两个生成 skill 都会把接口详情（方法、路径、参数、请求体字段、响应字段）拼进提示词，
所以模型写 `extract` 时知道该取 `id` 还是 `data.id`。

## REST 端点

```
GET    /api/platform/api-assets?project_id=
POST   /api/platform/api-assets/import
DELETE /api/platform/api-assets/{id}

GET    /api/platform/api-endpoints/modules?project_id=
GET    /api/platform/api-endpoints?project_id=&q=&method=&module=
POST   /api/platform/api-endpoints
GET    /api/platform/api-endpoints/{id}
PATCH  /api/platform/api-endpoints/{id}
DELETE /api/platform/api-endpoints/{id}
POST   /api/platform/api-endpoints/{id}/debug

GET    /api/platform/api-cases?project_id=&kind=
POST   /api/platform/api-cases/generate
POST   /api/platform/api-cases/generate-scenario
POST   /api/platform/api-cases
PATCH  /api/platform/api-cases/{id}
DELETE /api/platform/api-cases/{id}
POST   /api/platform/api-cases/{id}/run?base_url=

GET    /api/platform/api-runs?project_id=&limit=
GET    /api/platform/api-runs/{id}
POST   /api/platform/api-runs/{id}/diagnose
```

注意 `/api-endpoints/modules` 必须声明在 `/api-endpoints/{id}` 之前，否则 `modules` 会被当成 int 路径参数。

## 页面

`views/automation/ApiAutomationView.vue`，单页七页签：

- 顶部：接口数 / 用例数 / 近 60 次通过率，项目选择（记在 localStorage），刷新
- 接口资产：导入弹窗（粘贴 JSON 或 YAML），资产表带版本、Base URL、接口数
- 接口管理：方法彩色标签、搜索、方法/模块筛选、编辑/调试/删除
- 调试抽屉：Base URL、Headers/Query/body 三个 JSON 输入框、期望状态码、响应面板
- 单接口 Agent：选接口、生成条数、知识库，生成后直接进用例库
- 场景 Agent：多选接口 + 业务目标，生成后展示步骤链
- 单接口用例 / 接口场景：执行、启用、删除
- 执行记录：状态、状态码、耗时、详情抽屉（逐步 + AI 归因）

## 与目标站对照

| 目标站 | 本平台 | 差异 |
| --- | --- | --- |
| 接口资产（导入 OpenAPI） | 一致 | 未做多版本 diff |
| 接口管理（类 Postman 调试） | 一致 | 未做环境变量集管理 |
| 单接口 Agent | 一致 | — |
| 场景 Agent（数据流） | 一致 | 未做分支/循环 |
| 执行记录 + AI 归因 | 一致 | 未做批量并发执行 |
| 编排 Agent | 部分 | 场景即编排，缺可视化拖拽 |

## 下一步

Phase 5 做 UI 自动化：用例执行、探索生成脚本、环境变量注入、自由对话。
