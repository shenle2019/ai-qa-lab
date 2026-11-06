# Phase 3 测试记录

- 时间：2026-11-06
- 环境：Windows · Python 3.11（仓库 `.venv`）· SQLite `sut.db` · Chromium（playwright v1140）
- 服务：`python -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000 --reload`（后台 job `pwsh-ac2ba8fc2b5941c2`）

## 1. 单元 / 接口测试

```powershell
cd E:\ailearning\ai-qa-lab
.venv\Scripts\python.exe -m pytest apps/sut/backend/tests -q
```

```
101 passed, 1 warning in 3.28s
```

Phase 3 新增 `tests/test_knowledge.py`（11 条）：

| 用例 | 覆盖点 | 结果 |
| --- | --- | --- |
| `test_create_and_list_knowledge_base` | 建库返回分块参数，列表能查到 | pass |
| `test_duplicate_name_rejected` | 同项目同名 → 409 | pass |
| `test_create_requires_name` | 空名称 → 422 | pass |
| `test_add_text_document_chunks_and_lists` | 粘贴文本入库，分块数 ≥2，每块不超过 chunk_size，统计同步 | pass |
| `test_upload_document_extracts_text` | multipart 上传 md，`source=upload` | pass |
| `test_upload_without_text_rejected` | 二进制无文本 → 400 | pass |
| `test_search_returns_ranked_hits` | 检索命中，首条就是含「5000」的那块 | pass |
| `test_search_on_empty_base_returns_nothing` | 空库检索返回空数组而不是报错 | pass |
| `test_delete_document_and_base` | 删文档后分块归零，删库后 404 | pass |
| `test_knowledge_skills_registered_and_runnable` | 4 个 skill 注册且能跑通建库→写文档→检索 | pass |
| `test_search_skill_validates_payload` | 空 query → 400，库不存在 → 404 | pass |

Phase 0–2 的 90 条保持通过，无回归。

## 2. 真实冒烟（`scripts/phase3_smoke.py`）

真实文件：`docs/requirements/2026-11-06-ai-test-platform-refactor.md`。结果写 `docs/phases/phase-3/smoke-output.json`。

| 步骤 | 结果 |
| --- | --- |
| 创建知识库「平台重构方案库」 | 201，`chunk_size=500`、`chunk_overlap=80` |
| 上传 md | 5567 字符 → **19 块**，无提取备注 |
| 粘贴接口约定 | 1 块（短文档不硬切） |
| 分块抽样 | seq 0 = 495 字符，seq 1 = 102 字符，seq 2 = 500 字符 |
| 检索「导出超过 5000 条怎么处理」 | 2 条命中，`took_ms=3`，首条 `接口约定.md#0`，分数 0.33，片段正是 202 转后台任务那段 |
| skill 检索「匿名请求返回什么」 | total=2，`context` 正常拼出 `[文件#序号]` 前缀 |
| 最终统计 | 2 文档 / 20 分块 |

## 3. UI 端到端（playwright）

`scripts/phase3_visual_check.py`：

```
ok overview
ok search
ok chunks
```

截图（`docs/screenshots/`）：

| 文件 | 内容 |
| --- | --- |
| `phase3-kb-overview.png` | 知识库页初始态：左库列表、右文档表、试检索区，顶部 1/2/20 指标 |
| `phase3-kb-search.png` | 检索「导出超过 5000 条会怎么处理」，2 条命中带分数条，耗时 3ms |
| `phase3-kb-chunks.png` | 分块查看弹窗，覆盖层与 `#0 / 125 字符` 正常 |

页面无 `pageerror`。

## 4. 过程中发现并修掉的问题

| 问题 | 现象 | 修复 |
| --- | --- | --- |
| 新增路由 404 | `--reload` 在 main.py 变更的同一时刻重启，新进程仍拿着旧路由表 | 直接重启后台 job，验证 `/api/platform/knowledge-bases` 返回 200 |
| 204 端点启动即崩 | FastAPI 断言「Status code 204 must not have a response body」 | 删除接口改为 `return Response(status_code=204)`，并去掉 `-> None` |
| 弹窗没有遮罩 | 知识库页面用了 `.modal` + `.modal-body`，而项目里的约定是 `.modal-mask` + `.modal`（样式定义在 FunctionalView 的 scoped style 里） | 改成 `.modal-mask` + `.modal`，并在本页补一套 scoped 样式 |
| 工具条按钮被拉开 | `.toolbar` 是 space-between，三个子元素时中间空一大截 | 按钮包进 `.toolbar-group`，说明文字 `margin-left:auto` |

## 5. 复现步骤

```powershell
cd E:\ailearning\ai-qa-lab
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000 --reload
.venv\Scripts\python.exe -m pytest apps/sut/backend/tests -q
.venv\Scripts\python.exe scripts\phase3_smoke.py
python scripts\phase3_visual_check.py
```
