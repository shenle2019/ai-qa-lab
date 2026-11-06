# Phase 0 · 骨架与可扩展底座

> 目标：把 `ai-qa-lab` 从「一套写死的测试页面」改成「一个有 Skill 注册表的测试平台骨架」，侧栏结构与 RainaAI 测试平台对齐，后续每个模块只需注册 skill + 填充页面即可扩展。

## 1. 本阶段交付

| 交付物 | 位置 | 状态 |
| --- | --- | --- |
| Skill 注册表（后端） | `apps/sut/backend/app/skills/registry.py` | ✅ |
| 内置 skill ×3 | `apps/sut/backend/app/skills/builtin/` | ✅ |
| Skill HTTP 接口 | `apps/sut/backend/app/skills_api.py` | ✅ |
| 路由注册 | `apps/sut/backend/app/main.py:56` | ✅ |
| 侧栏 5 组重构 | `apps/sut/frontend/src/App.vue` | ✅ |
| 新路由 ×13 | `apps/sut/frontend/src/router.js` | ✅ |
| 新页面 ×13 | `apps/sut/frontend/src/views/{projects,ai,testing,automation}/` | ✅ |
| 前端 API 封装 | `apps/sut/frontend/src/api/client.js` | ✅ |
| 分组侧栏样式 | `apps/sut/frontend/src/style.css`（末尾 Grouped sidebar 段） | ✅ |
| 后端测试 | `apps/sut/backend/tests/test_skills_registry.py` | ✅ 8 条 |

## 2. 侧栏结构（对齐目标站）

```
工作台      项目管理 / 系统 AI 配置 / AI 调用日志 / 用户管理
当前项目    项目概览
测试        需求管理 / 功能测试 / 知识库
自动化      环境管理 / 接口自动化 / UI 自动化
项目        模块管理 / 成员管理
开发工具    仪表盘 / 工单 / API 工作台 / 知识库问答 / 测试平台 / 模型中心 / 测试用例 / 方法论 / 项目报告 / 模块验收（收起）
```

旧页面全部保留（路由未删），收进「开发工具」折叠组，避免回归。

## 3. Skill 注册表设计

```python
@dataclass
class Skill:
    id: str                 # 全局唯一，如 case.generate
    name: str               # 中文名
    category: str           # case / project / requirement / api / ui / kb ...
    description: str
    input_schema: dict      # JSON Schema（前端据此渲染表单）
    output_schema: dict
    handler: Callable[[payload, ctx], Any]
    version: str = "0.1.0"
    enabled: bool = True
    source: str = "builtin" # builtin | external
```

- `register(skill)`：注册/覆盖。
- `list_skills(category, include_disabled)`：按分类过滤，只返回启用项。
- `run_skill(skill_id, payload, ctx)`：`ctx` 里带 `db`，handler 直接复用现有业务代码。
- 失败统一抛 `SkillError(message, status_code)`，API 层转 `HTTPException`。

### HTTP 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/platform/skills?category=` | 列出 skill 描述（含 input_schema） |
| GET | `/api/platform/skills/{id}` | 单个描述 |
| POST | `/api/platform/skills/{id}/run` | 执行，body 即 payload |

### 内置 skill（Phase 0）

| id | category | 说明 |
| --- | --- | --- |
| `case.generate` | case | 复用 `case_generator.generate`，输入需求 → 生成 draft 用例 |
| `case.list` | case | 按项目查用例 |
| `project.list` | project | 列出全部项目 |

> 扩展方式：新增一个 `app/skills/builtin/xxx.py`，定义 `SKILL = register(Skill(...))`，在 `builtin/__init__.py` 里 import 一行即可；前端无需改代码，`系统 AI 配置` / `项目概览` 会按 category 自动列出。

## 4. 页面清单

| 路由 | 页面 | 状态 |
| --- | --- | --- |
| `/` `/overview` | 项目概览 | 真实数据（summary + skills 列表） |
| `/projects` | 项目管理 | 真实数据（列表 + 创建） |
| `/system-ai` | 系统 AI 配置 | 大模型 Tab 真实；向量 / Midscene 占位 |
| `/ai-logs` | AI 调用日志 | 真实数据（最近 20/50/100 条） |
| `/functional` | 功能测试 | 真实数据（skill 驱动生成 + 用例列表） |
| `/requirements` | 需求管理 | 占位（Phase 1） |
| `/kb` | 知识库 | 占位（Phase 3） |
| `/environments` | 环境管理 | 占位（Phase 4） |
| `/api-automation` | 接口自动化 | 占位（Phase 3） |
| `/ui-automation` | UI 自动化 | 占位（Phase 4） |
| `/modules` `/members` `/users` | 模块 / 成员 / 用户 | 占位（Phase 5） |

## 5. 不在本阶段范围

- 需求上传与 AI 分析（Phase 1）
- 知识库分块与检索（Phase 3）
- OpenAPI 导入、接口调试、场景编排（Phase 3）
- midscene / UI 脚本执行（Phase 4）
- 真正的账号体系与权限（Phase 5）

## 6. 下一步

Phase 1：需求管理落地（`requirement.create / analyze / plan` 三个 skill + 上传 + 右侧对话 Agent + 测试计划）。
