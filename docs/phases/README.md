# 重构阶段索引（Phase 0–5）

把 `ai-qa-lab` 从「单页工作台」重构成 Raina《AI 测试平台》那套结构：**项目为容器，测试能力全部以 skill 注册，页面只负责编排**。

每个阶段都有三份文件，缺一不算完成：

- `README.md` —— 做了什么、数据模型、skill 契约、端点、页面
- `test-record.md` —— 命令、结果、真实链路数据、截图、问题与修复
- `test-report.md` —— 指标、验收对照、优点、不足、风险、结论

## 阶段总表

| 阶段 | 主题 | 核心产出 | 测试 | 文档 |
| --- | --- | --- | --- | --- |
| P0 | 骨架与 skill 注册表 | `skills/registry.py`、`skills_api.py`、5 组侧栏、13 个新路由 | 72 passed | [phase-0](phase-0/README.md) |
| P1 | 需求管理 | 需求三表、文件文本提取（md/txt/docx/pdf）、`requirement.analyze/plan/chat` | 82 passed | [phase-1](phase-1/README.md) |
| P2 | 功能测试 | `case.update/batch`、批量评审状态机、AI 生成 + 需求库联动 | 90 passed | [phase-2](phase-2/README.md) |
| P3 | 知识库 | 分块、词面检索、`kb.*` 四件套、试检索页 | 101 passed | [phase-3](phase-3/README.md) |
| P4 | 接口自动化 | OpenAPI 导入、接口调试、单接口/场景 Agent、执行与 AI 归因 | 118 passed | [phase-4](phase-4/README.md) |
| P5 | UI 自动化 + 管理面 | Playwright 执行、探索生成、脚本导出、系统 AI 三分类、模块/成员/用户 | 135 passed | [phase-5](phase-5/README.md) |

## 全局统计

| 项 | 数值 |
| --- | --- |
| 注册 skill | 19 个（case 4、requirement 3、kb 4、api 4、ui 3、project 1） |
| `/api/platform` 端点 | 101 条 |
| 后端测试 | 135 条全通过 |
| 前端页面 | 17 个路由（5 组侧栏 + 开发工具折叠组） |
| 截图 | `docs/screenshots/`，phase0–phase5 共 40+ 张 |

## 架构主线

```
app/
├── skills/                 # 能力层：只认 payload，不认 HTTP
│   ├── registry.py         # Skill dataclass + register/run_skill
│   └── builtin/            # 19 个内置 skill
├── *_models.py             # 按域拆表的 SQLAlchemy 模型
├── *_api.py                # 按域拆的 APIRouter，全部 /api/platform 前缀
├── api_openapi.py          # OpenAPI(JSON/YAML) → endpoints
├── api_runner.py           # 请求渲染、{{变量}} 替换、断言
├── api_executor.py         # 用例/场景执行 + AI 归因
├── ui_steps.py             # 11 种 UI 动作 + normalise + 脚本渲染
├── ui_runner.py            # Playwright 真跑 + 页面快照
└── main.py                 # create_all + ensure_columns + 挂 9 个 router
```

三条约定：

1. **新增能力 = 新增一个 skill 文件**，前端 `GET /api/platform/skills?category=` 自动渲染，不改页面逻辑。
2. **页面只编排**：不写业务判断，校验与状态流转都在 skill 里，方便被外部脚本直接调用。
3. **真实链路验证**：每个阶段除了单测，都跑一遍「真实模型 + 真实 HTTP/浏览器」的冒烟，数据落在 `docs/phases/phase-N/smoke-output.json`。

## 与目标站（RainaAI 测试平台）的对照

| 目标站区域 | 本平台 | 差距 |
| --- | --- | --- |
| 工作台：项目管理 / 系统 AI 配置 / AI 调用日志 / 用户管理 | 全部落地 | 用户管理只是目录，未做权限拦截 |
| 当前项目：概览 | 项目概览（6 指标 + skill 表） | 无 |
| 测试：需求管理 / 功能测试 / 知识库 | 全部落地，需求三列布局对齐 | 知识库为词面检索，无向量 |
| 自动化：环境管理 / 接口自动化 / UI 自动化 | 接口与 UI 落地；环境管理仍是占位 | 环境管理未做（环境变量分散在各用例） |
| 项目：模块管理 / 成员管理 | 落地 | 无 |
| UI 套件 / 录制 / midscene 识图 | 未做 | P5 已知不足 |

## 尚未覆盖（下一轮）

1. **环境管理**：目标站把「环境」当一等对象（base_url + 变量集），当前只能逐用例填。
2. **UI 套件**：多条用例顺序执行 + 汇总报告。
3. **录制**：浏览器点一遍生成 `steps_json`。
4. **向量检索**：知识库接 embedding + 向量库，替换词面匹配。
5. **异步执行**：长用例应进队列，避免 HTTP 超时。
