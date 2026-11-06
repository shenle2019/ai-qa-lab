# Phase 2 测试记录

- 时间：2026-11-06
- 环境：Windows · Python 3.11（仓库 `.venv`）· Node 20 · SQLite `sut.db` · Chromium（playwright v1140）
- 服务：`python -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000 --reload`（后台 job `pwsh-356695d9856b4631`）

## 1. 单元 / 接口测试

命令：

```powershell
cd E:\ailearning\ai-qa-lab
.venv\Scripts\python.exe -m pytest apps/sut/backend/tests -q
```

结果：

```
90 passed, 1 warning in 3.02s
```

Phase 2 新增 `apps/sut/backend/tests/test_case_management.py`（8 条）：

| 用例 | 覆盖点 | 结果 |
| --- | --- | --- |
| `test_patch_case_updates_fields` | PATCH 改标题/优先级，落库生效 | pass |
| `test_patch_case_rejects_bad_payload` | 空 payload → 400；不存在 → 404 | pass |
| `test_get_and_delete_case` | GET 详情 + DELETE → 204，再 GET → 404 | pass |
| `test_batch_review_flow` | draft → submit_review → approve，并写入 review 记录 | pass |
| `test_batch_skips_cases_in_wrong_status` | 状态不符进 `skipped`，reason 可读 | pass |
| `test_batch_delete_and_validation` | 批量删除；非法 action → 400 | pass |
| `test_generate_cases_from_requirement_analysis` | 传 `requirement_id` 时 prompt 里带功能点，生成 draft | pass |
| `test_case_skills_are_registered` | 注册表含 4 个 case skill | pass |

Phase 0/1 原有 82 条全部保持通过，无回归。

## 2. 真实冒烟（`scripts/phase2_smoke.py`）

真实 HTTP 调用 + 真实大模型，结果写 `docs/phases/phase-2/smoke-output.json`。

| 步骤 | 结果 |
| --- | --- |
| `POST /cases` | 201，id 20 |
| `PATCH /cases/20` | 200，标题已改 |
| 批量 `draft` / `submit_review` / `approve` | 各 `updated: 1`，`skipped: []` |
| `GET /cases/20/reviews` | 1 条，reviewer `smoke`，decision `approved` |
| `POST /skills/case.generate/run`（`requirement_id=1`） | 200，模型 `deepseek-chat`，生成 4 条，全部 `draft`，`has_steps: true` |
| 批量删除生成结果 | `updated: 4` |
| `DELETE /cases/20` | 204 |

生成出的标题示例：`管理员按状态筛选工单列表`、`非管理员请求导出接口返回无权限`、`管理员导出5000条直接下载` —— 能看出 prompt 确实吃到了需求分析里的功能点。

## 3. UI 端到端（playwright）

`scripts/phase2_visual_check.py`：

```
ok manage
ok batch bar
ok edit modal
ok generate tab
```

`scripts/phase2_generate_shot.py`：在浏览器里选需求 → 点「AI 生成用例」→ 等真实模型返回，页面提示 `已生成 10 条草稿（模型 deepseek-chat），确认后可提交审核`，右侧预览出 10 张卡片（标题 / 模块 / 优先级 / 步骤 / 预期）。

截图（`docs/screenshots/`）：

| 文件 | 内容 |
| --- | --- |
| `phase2-case-manage.png` | 用例管理列表，9 条，状态徽章（已通过 / 待审核 / 草稿） |
| `phase2-case-batch.png` | 勾选 2 条后的批量栏（选 2 / 提交审核 / 通过 / 驳回 / 退回草稿 / 删除） |
| `phase2-case-edit.png` | 编辑弹窗，步骤与预期结果已从详情接口补全 |
| `phase2-case-generate.png` | AI 生成 Tab 初始态 |
| `phase2-case-generate-result.png` | 真实生成 10 条草稿后的预览 |

页面无 `pageerror`。

## 4. 过程中发现并修掉的问题

| 问题 | 现象 | 修复 |
| --- | --- | --- |
| 编辑弹窗步骤/预期为空 | 列表接口只返回 id/标题/模块/优先级/状态 | `openEdit` 改为先占位再拉 `GET /cases/{id}` 补全 |
| 工具条控件竖排 | 全局 `select { width: 100% }` 让每个控件占满一行 | `.toolbar select { width: auto; min-width: 160px }` |
| 复选框显示成大白块 | 全局 input 样式作用到了 checkbox | `.check-col input[type=checkbox] { width:14px; height:14px }` |
| 截图里只有一个调试项目 | 早前调试脚本留下的 `dbg-x1` | 删项目 3 及其用例 |
| CSS 变量不存在 | 用了 `--text-dim` / `--bg-soft` | 改回根变量 `--muted` / `--panel` |
| 批量路由 422 | `/cases/batch` 写在 `/cases/{case_id}` 之后被当成 int 解析 | 把 `POST /cases/batch` 声明提前 |

另记两条环境经验：

- `POST /cases` 默认 `status="approved"`（历史行为），写测试不能假设新用例是 `draft`。
- `case_generator._normalize_step` 会强校验「HTTP 方法 + 路径 + `status=` 断言」，mock 数据不满足会报「模型没有返回有效用例」。

## 5. 复现步骤

```powershell
cd E:\ailearning\ai-qa-lab
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000 --reload
.venv\Scripts\python.exe -m pytest apps/sut/backend/tests -q
.venv\Scripts\python.exe scripts\phase2_smoke.py
python scripts\phase2_visual_check.py
python scripts\phase2_generate_shot.py
```
