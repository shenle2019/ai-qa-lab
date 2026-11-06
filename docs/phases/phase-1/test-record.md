# Phase 1 · 测试记录

> 记录时间：2026-11-06
> 被测版本：`v1.2.0 · Phase 1`
> 运行环境：Windows / Python `.venv` / Node 24 / SQLite `sut.db`

## 0. 环境与启动

```powershell
cd E:\ailearning\ai-qa-lab
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000 --reload
```

`.env` 由 `settings.py::_load_dotenv()` 自动加载（不需要手工注入环境变量）；数据库为仓库根目录的 `sut.db`（`DATABASE_URL` 是相对路径，脚本必须在仓库根运行）。

## 1. 自动化测试（pytest）

| 命令 | 结果 |
| --- | --- |
| `.venv\Scripts\python.exe -m pytest apps/sut/backend/tests/test_requirements.py -q` | 10 passed |
| `.venv\Scripts\python.exe -m pytest apps/sut/backend/tests -q` | **82 passed**, 1 warning, 2.78s |

`test_requirements.py` 覆盖：

| # | 用例 | 断言要点 |
| --- | --- | --- |
| 1 | 创建并列出需求 | 201 / 字段回显 / 列表包含 |
| 2 | 缺标题或项目 | 422 |
| 3 | 更新与删除 | PATCH 生效、DELETE 后 404 |
| 4 | txt 附件上传 | `extracted_text` 有内容、`chars > 0`、可下载 |
| 5 | 未知后缀附件 | 200，`extract_note` 非空，不抛错 |
| 6 | analyze | 分析写入库，status → `analyzed` |
| 7 | 未分析先 plan | 409 |
| 8 | plan | 落库 + 创建 `TestPlan` |
| 9 | chat 落库 | 用户/助手两条消息 |
| 10 | chat 更新分析 | `analysis_updated=true`、库中 summary 被覆盖、**回复与消息正文都不含 ```json 块** |

LLM 全部通过 `monkeypatch.setattr("app.llm_client.chat_json" | "app.llm_client.chat_text", fake)` 打桩，测试不联网、不花钱。

## 2. 端到端冒烟（真实大模型）

```powershell
.venv\Scripts\python.exe scripts\phase1_smoke.py
```

| 步骤 | 结果 |
| --- | --- |
| 创建需求 | 201 |
| 需求分析 | 200 |
| 测试计划 | 200 |
| 对话修订 | 200 |
| 健康检查 | `{"status":"ok","service":"sut","version":"1.1.0"}` |

产出（`docs/phases/phase-1/smoke-output.json`）：

- 分析：**9 条功能清单 / 3 个界面 / 7 条待澄清 / 8 条风险**，summary 正常（含"超过 5000 条转后台任务""UTF-8 BOM"等约束，说明模型吃到了正文细节）。
- 计划：**3.5 人天 / 4 个里程碑**，并创建 `TestPlan id=3`《工单列表支持状态筛选、排序与 CSV 导出 · 测试计划》。
- 对话：回复 **3179 字**，`analysis_updated=true`，消息数 2，最终状态 `planned`，`has_analysis`/`has_plan` 均为 true。

> 注：同为「工单列表增强」需求，两次真实运行分别得到 12/2/8/9 与 9/3/7/8 的结构化条目数，属大模型正常波动，不影响功能正确性。

## 3. 视觉验证（Playwright）

```powershell
python scripts\phase1_visual_check.py
```

| 截图 | 内容 | 结论 |
| --- | --- | --- |
| `docs/screenshots/phase1-requirements-list.png` | 需求列表（hero 指标 + 筛选 + 表格） | 正常 |
| `docs/screenshots/phase1-requirement-detail.png` | 详情三列（正文/分析 Tabs/助手） | 布局对齐目标站 |
| `docs/screenshots/phase1-requirement-plan.png` | 测试计划 Tab | 里程碑与范围渲染正常 |
| `docs/screenshots/phase1-requirement-clarify.png` | 待澄清 Tab | 问题 + 原因成对渲染 |

无 `pageerror`；1440×1000 视口下三列不挤压，1200px 以下降为单列。

## 4. 回归

- 旧接口全量测试仍在同一套件内跑（`test_platform*.py`、`test_case_generation.py`、`test_execution.py`、`test_model_center.py`、`test_tickets.py`、`test_security.py`、`test_health.py`、`test_skills_registry.py`），**全部通过**，未出现回归。
- 前端 `npm run build` 成功，无未使用导入告警导致的构建失败。

## 5. 本轮发现的问题与修复

| # | 问题 | 现象 | 修复 |
| --- | --- | --- | --- |
| 1 | 重启后 AI 生成报「未配置 API Key」 | `case.generate` 返回 502 | `settings.py` 加 `_load_dotenv()`，模块导入即加载仓库根 `.env` |
| 2 | 聊天记录里出现裸 ```json 块 | 助手消息把机器用的分析 JSON 直接显示给用户 | `requirement_chat.py` 用 `re.sub(r"```json\s*.*?```", "", reply, flags=re.S)` 清洗后再入库，并补「（分析结果已更新）」提示 |
| 3 | reload 未生效导致脏数据 | 首轮 chat 跑在旧进程上，写入未清洗的回复 | 已清空该需求的对话消息并重发一次，验证回复不含 ```json |
| 4 | `pypdf` 装不上（要求 5.1.0 与当前环境冲突） | `pip install pypdf` 失败 | PDF 改走零依赖 `zlib` 方案，扫描件/加密件给降级提示 |

## 6. 复现清单

```powershell
cd E:\ailearning\ai-qa-lab
.venv\Scripts\python.exe -m pytest apps/sut/backend/tests -q
.venv\Scripts\python.exe scripts\phase1_smoke.py
python scripts\phase1_visual_check.py
cd apps/sut/frontend; npm run build
```
