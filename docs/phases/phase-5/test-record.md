# Phase 5 · 测试记录

## 1. 环境

| 项 | 值 |
| --- | --- |
| 仓库 | `E:\ailearning\ai-qa-lab` |
| Python | `.venv\Scripts\python.exe`（3.11） |
| pytest | 全量 `pytest apps/sut/backend/tests -q` |
| Playwright | `playwright 1.64.1`（装在 `.venv`），浏览器 `chromium-1248` 放在 `E:\ailearning\ai-qa-lab\.pw-browsers` |
| 服务 | `python -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000`（不挂 `--reload`，改代码后手动重启） |
| 数据库 | `sut.db`（SQLite，相对仓库根目录） |
| 截图脚本 | 系统 Python 3.8（`playwright` 1.4x + chromium v1140），`scripts/phase5_*.py` |

## 2. 自动化测试

### 2.1 全量

```
$ .venv\Scripts\python.exe -m pytest apps/sut/backend/tests -q
135 passed, 1 warning in 9.42s
```

对比 Phase 4 的 118 条，本阶段新增 17 条：`test_ui_automation.py` 11 条、`test_users.py` 6 条。

### 2.2 `test_ui_automation.py`（11 条）

| 用例 | 断言要点 |
| --- | --- |
| `test_create_and_list_ui_case` | 建用例 201、列表能查到、`steps` 归一化 |
| `test_bad_action_rejected` | `action=explode` → 400 |
| `test_bad_status_rejected` | `status=whatever` → 400 |
| `test_script_export` | `/script` 返回含 `sync_playwright` 与 `goto` 的脚本 |
| `test_run_records_success` | monkeypatch `execute_case` → `ui_runs.status=passed` |
| `test_run_records_failure` | monkeypatch 抛 `RunError` → `status=failed` 且记录 error |
| `test_run_missing_case` | 不存在 case_id → 404 |
| `test_explore_saves_draft` | patch `snapshot` + `chat_json`，落库 `source=ai`、`status=draft` |
| `test_explore_requires_goal` | 空 goal → 422 |
| `test_chat_returns_reply` | patch `snapshot` + `chat_text`，返回 `answer` |
| `test_step_helpers` | `normalise_steps` / `parse_env` 边界（空数组、非数组、超 40 步） |

### 2.3 `test_users.py`（6 条）

建/列、同名 409、空名 400、非法角色与状态 400、PATCH+DELETE（删除后 PATCH 404）、`/health` 暴露 `auth` 字段。

## 3. 真实链路验证

| 步骤 | 结果 |
| --- | --- |
| `scripts/phase5_check.py`：手工用例 CRUD → 执行 → 导出脚本 → 404 → AI 探索 → AI 对话 | 全部 200/201，脚本含 `page.goto` |
| `scripts/phase5_demo.py`：清空 project 2 的 UI 用例 → 在真实 UI 点「AI 生成用例」→ 点「执行」 | 生成 case #1（3 步，`source=ai`）；执行 run #1 `passed`，174 ms |
| `scripts/phase5_project_seed.py`：项目 2 建 3 模块 / 3 成员 / 2 个非 chat 模型 | modules 3、members 3、embedding 1、vision 1 |
| 平台账号 | `沈乐（管理员）`、`张三（测试）`，列表 2 条 |

AI 探索实际产出（`#/kb` 知识库页）：

```
目标：打开知识库页面，确认页面上出现「试检索」入口
1. goto           http://127.0.0.1:8000/ui/#/kb
2. assert_visible text=试检索
3. assert_text    body → 输入问题，看命中的分块与相关度
```

## 4. 截图

| 文件 | 内容 |
| --- | --- |
| `phase5-ui-explore.png` | AI 探索：39 个元素 + 3 步生成结果 |
| `phase5-ui-cases.png` | UI 用例表（AI 草稿 + 手工已就绪） |
| `phase5-ui-runs.png` | 执行记录表 |
| `phase5-ui-run-detail.png` | 执行详情（逐步状态 + 失败截图） |
| `phase5-ui-case-edit.png` | 用例编辑弹窗 |
| `phase5-ui-case-script.png` | 导出的 Playwright 脚本 |
| `phase5-system-ai.png` / `-embedding.png` / `-midscene.png` | 系统 AI 配置三分类 |
| `phase5-modules.png` / `phase5-members.png` / `phase5-users.png` | 模块 / 成员 / 用户管理 |
| `phase5-ai-logs.png` | AI 调用日志 |

## 5. 问题与修复

| # | 现象 | 根因 | 修复 |
| --- | --- | --- | --- |
| 1 | 后端 import `app.registry` 失败 | skill 在 `skills/builtin/`，三层相对导入指错 | 改成 `from ..registry import ...` |
| 2 | 弹窗无背景遮罩 | `.modal-mask/.modal` 定义在 `FunctionalView.vue` 的 scoped style 里，不跨组件生效 | 在 `UiAutomationView.vue` / `UsersView.vue` 各自补一份 scoped 样式 |
| 3 | AI 生成的用例必然失败：`strict mode violation: locator("text=知识库") resolved to 9 elements` | Playwright strict mode 不允许一个选择器命中多个元素 | `_locator()` 统一 `.first` |
| 4 | `test_explore_saves_draft` / `test_chat_returns_reply` 报「没有启用的模型」 | 测试用内存库，没有模型配置 | 加 `llm_ready` fixture，缺模型时先 POST 一套 fake 配置 |
| 5 | `test_step_helpers` 报 `至少要有一步` | `normalise_steps([])` 被当成非法 | 空数组合法返回 `[]`，空步骤校验下沉到 skill |
| 6 | 端口 8000 被占：`[Errno 10048]` | 之前用 `--reload` 起的进程没被 job_kill 干净 | `Get-NetTCPConnection -LocalPort 8000 -State Listen` 取 PID 再 `Stop-Process -Force` |
| 7 | `<select>` 在 Windows Chrome 上白底白字 | 原生下拉忽略 `background` | `appearance:none` + 自绘箭头（`style.css` 末尾） |
| 8 | 模块页默认选中 project 3（0 条） | 项目下拉取第一条，名称排序把「自动化测试项目」排前 | 截图脚本显式选「执行验证项目」 |

## 6. 复现命令

```powershell
cd E:\ailearning\ai-qa-lab
.venv\Scripts\python.exe -m pytest apps/sut/backend/tests -q

# 服务
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000

# 前端
cd apps/sut/frontend; npm run build

# 演示与截图
python scripts\phase5_project_seed.py
python scripts\phase5_admin_shots.py
python scripts\phase5_demo.py
```
