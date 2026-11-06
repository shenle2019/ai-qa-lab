# Phase 5 · UI 自动化 + 平台管理面

> 目标站对应区域：`自动化 / UI 自动化`、`工作台 / 系统 AI 配置`、`工作台 / 用户管理`、`项目 / 模块管理`、`项目 / 成员管理`。

Phase 5 收掉两件事：

1. **UI 自动化**：用 Playwright 真跑浏览器，AI 通过抓取真实页面快照生成可执行步骤，环境变量注入 `localStorage` 免登录，失败留截图，跑完可导出独立脚本。
2. **平台管理面**：把之前只有占位页的「系统 AI 配置（大模型 / 向量模型 / Midscene 三分类）」「模块管理」「成员管理」「用户管理」做成真实功能。

## 1. 交付清单

| 模块 | 页面路由 | 后端 | 状态 |
| --- | --- | --- | --- |
| UI 自动化 | `/ui-automation` | `ui_api.py` + `ui_runner.py` + `ui_steps.py` | 已完成 |
| 系统 AI 配置 | `/system-ai` | `model_api.py`（新增 `kind` 分类） | 已完成 |
| 模块管理 | `/modules` | `project_content_api.py` | 已完成 |
| 成员管理 | `/members` | `project_content_api.py` | 已完成 |
| 用户管理 | `/users` | `users_api.py` | 已完成 |
| AI 调用日志 | `/ai-logs` | `model_api.py`（已有 `model_calls`） | 已完成（Phase 0 落地，本阶段接入真实数据） |

## 2. 数据模型

### 2.1 `ui_cases`（UI 用例）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int PK | |
| project_id | int FK `platform_projects.id` | 所属项目 |
| title | varchar(200) | 用例名 |
| module | varchar(80) | 分组，AI 生成的默认 `AI 探索` |
| kind | varchar(20) | `case` / `suite`（预留） |
| base_url | varchar(500) | 起始地址 |
| env_json | text | `localStorage` 注入，形如 `{"token":"abc"}` |
| steps_json | text | 步骤数组，见 2.3 |
| status | varchar(20) | `draft` / `ready` / `archived` |
| source | varchar(20) | `manual` / `ai` |
| prompt_version | varchar(40) | AI 生成时记录的提示词版本 |
| note | text | AI 给的理由（reasoning） |

### 2.2 `ui_runs`（执行记录）

`id / project_id / case_id / title / status(passed|failed|running) / duration_ms / steps_json / screenshot / error / created_at`。

`screenshot` 存相对路径 `data/ui-shots/ui-run-{run_id}.png`；接口 `/api/platform/ui-runs/{id}` 额外返回 `screenshot_data`（base64），因为 `<img>` 标签带不了 `Authorization` 头。

### 2.3 步骤格式（`ui_steps.py`）

```json
[
  {"action": "goto", "target": "http://127.0.0.1:8000/ui/#/projects"},
  {"action": "assert_visible", "target": "text=项目管理"},
  {"action": "fill", "target": "input[placeholder='项目名称']", "value": "演示项目"},
  {"action": "wait", "ms": 500}
]
```

- 支持 11 种动作：`goto / click / fill / press / select / hover / wait / assert_text / assert_visible / assert_url / screenshot`
- `normalise_steps` 负责清洗：非数组报错、最多 40 步、`wait.ms` 夹到 `0–30000`、`timeout` 夹到 `500–60000`
- `render_script()` 把同一份步骤渲染成可单独运行的 Playwright Python 脚本（含 `context.add_init_script` 注入 localStorage），页面「脚本」按钮直接展示

## 3. 执行引擎

`ui_runner.py`：

1. `snapshot(url, env)`：开无头 Chromium，注入环境变量，抓 `{title, url, text(前 3000 字), nodes(最多 80 个可交互元素)}`；`nodes` 覆盖 `a / button / input / select / textarea / [role=button]`，每个节点带 `tag / text / name / id / placeholder / type / role / href`。
2. `execute_case(case, run_id)`：按步骤顺序执行，失败即停，把首错写入 `error`，并在失败瞬间截 `ui-run-{run_id}.png`。
3. 定位统一走 `page.locator(target).first` —— `text=知识库` 这类选择器会同时命中侧栏和标题，Playwright 默认 strict mode 会直接报错，加 `.first` 后与人在浏览器里的直觉一致。

浏览器不装到 C 盘：`PLAYWRIGHT_BROWSERS_PATH=E:\ailearning\ai-qa-lab\.pw-browsers`（`ui_runner` 里用 `os.environ.setdefault` 兜底），已安装 `chromium-1248`。

## 4. Skill 契约

| id | category | 输入 | 输出 |
| --- | --- | --- | --- |
| `ui.case.generate` | `ui` | `url`、`goal`、`project_id`、`env`、`model_id`、`save` | `{reasoning, steps, page:{title,nodes}, case?}` |
| `ui.run` | `ui` | `case_id`、`headless` | `{run, steps, screenshot}` |
| `ui.chat` | `ui` | `url`、`question`、`env`、`model_id` | `{answer, page:{title,nodes}}` |

三个 skill 都可以在 `/api/platform/skills` 里查到、被任意前端或外部脚本调用。

## 5. REST 端点

**UI 自动化（9 条）**

```
GET    /api/platform/ui-cases?project_id=
POST   /api/platform/ui-cases
GET    /api/platform/ui-cases/{id}
PATCH  /api/platform/ui-cases/{id}
DELETE /api/platform/ui-cases/{id}
GET    /api/platform/ui-cases/{id}/script
POST   /api/platform/ui-cases/{id}/run
GET    /api/platform/ui-runs?project_id=
GET    /api/platform/ui-runs/{id}
GET    /api/platform/ui-runs/{id}/screenshot
POST   /api/platform/ui-explore
POST   /api/platform/ui-chat
```

**管理面（8 + 6 条）**

```
GET/POST        /api/platform/modules      PATCH/DELETE /api/platform/modules/{id}
GET/POST        /api/platform/members      PATCH/DELETE /api/platform/members/{id}
GET/POST        /api/platform/users        PATCH/DELETE /api/platform/users/{id}
```

`/api/platform/models` 增加 `kind` 维度：`chat`（大模型）、`embedding`（向量）、`vision`（Midscene）；`GET /api/platform/models?kind=embedding` 只返回该分类，`resolve_model()` 在生成用例时优先挑 `kind="chat"` 且启用的那套。

## 6. 前端

- `views/automation/UiAutomationView.vue`（约 340 行）：hero 三指标（UI 用例 / 已就绪 / 近 20 次通过率）+ 项目下拉（`localStorage: aiqa.ui.project`）+ 三 Tab：
  - **AI 探索**：左表单（页面地址 / 测试目标 / 环境注入 JSON）+ 右结果（页面标题·元素数 / reasoning / 步骤列表），生成后自动落草稿；下方「自由对话」就当前页面提问。
  - **UI 用例**：表格列 `ID / 名称 / 模块 / 环境注入 / 脚本步数 / 状态 / 来源 / 创建时间 / 操作`，操作含 编辑、执行、脚本、删除。
  - **执行记录**：`ID / 用例 / 结果 / 耗时 / 步骤 / 时间 / 详情`，详情弹窗展示每步状态与失败截图。
- `views/ai/SystemAiView.vue`：三 Tab 共用一套表格与注册表单，切换 Tab 时套用该分类的默认 Base URL 与模型名。
- `views/projects/ModulesView.vue` / `MembersView.vue`：项目下拉 + 新建表单 + 表格 + 编辑弹窗。
- `views/ai/UsersView.vue`：平台账号目录（用户名 / 邮箱 / 角色 / 状态 / 备注），顶部显示当前鉴权模式（`/health` 返回的 `auth`）。
- `style.css` 末尾补了 `select` 的统一样式：Windows Chrome 原生下拉会忽略深色背景，改成 `appearance:none` + 自绘箭头。

## 7. 与目标站对齐

| 目标站元素 | 本平台 | 备注 |
| --- | --- | --- |
| `UI 自动化 Agent / UI 用例 / UI 套件 / 执行记录` | `AI 探索 / UI 用例 / 执行记录` | 套件暂未拆，`kind=suite` 已预留 |
| `新建用例 / 录制` | `新建用例`（表单） | 录制（点点点生成脚本）未做，用 AI 探索替代 |
| `环境注入：不注入 / 跟随环境注入` | `env_json` 直接写 localStorage | 语义等价，粒度更细 |
| `脚本：已编写` | `脚本` 按钮导出 Playwright 脚本 | 一致 |
| `midscene 视觉识别` | Midscene 作为 `kind=vision` 的模型登记 | 识图执行未接，先占位分类 |
| `系统 AI 配置` 三 Tab | 三 Tab，且各自独立列表 | 一致 |
| `模块管理 / 成员管理 / 用户管理` | 三个真实页面 | 一致 |

## 8. 尚未完成

- **UI 套件**：现在只有单条用例执行，没有「多条用例组成套件、按顺序跑、汇总报告」。
- **录制**：目标站的「录制」是浏览器里点一遍就生成步骤，当前只能 AI 探索或手写 JSON。
- **视觉识别执行**：Midscene 只做了模型登记，尚未接入「用截图 + 视觉模型点击坐标」的降级链路。
- **权限**：用户管理只是目录，没有真正按角色拦截写接口。

## 9. 下一步

Phase 5 结束后进入收尾：补齐总验收文档、把 6 个 Phase 的 README 汇成一个索引、跑一遍全链路演示。
