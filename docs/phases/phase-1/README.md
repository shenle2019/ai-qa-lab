# Phase 1 · 需求管理（上传 → AI 分析 → 测试计划 → 对话修订）

> 目标：把目标站「需求管理」模块从占位页做成真实可用链路——传需求文档、AI 拆出功能清单/界面描述/待澄清项/风险、一键出测试计划（含人天），右侧对话 Agent 直接改分析结果。

## 1. 本阶段交付

| 交付物 | 位置 | 状态 |
| --- | --- | --- |
| 需求数据模型（3 张表） | `apps/sut/backend/app/requirement_models.py` | ✅ |
| 请求/响应模型 | `apps/sut/backend/app/requirement_schemas.py` | ✅ |
| 零依赖文本提取（md/txt/docx/pdf） | `apps/sut/backend/app/requirement_files.py` | ✅ |
| 需求 REST 接口 | `apps/sut/backend/app/requirement_api.py` | ✅ |
| skill `requirement.analyze` | `apps/sut/backend/app/skills/builtin/requirement_analyze.py` | ✅ |
| skill `requirement.plan` | `apps/sut/backend/app/skills/builtin/requirement_plan.py` | ✅ |
| skill `requirement.chat` | `apps/sut/backend/app/skills/builtin/requirement_chat.py` | ✅ |
| 纯文本 LLM 调用 | `apps/sut/backend/app/llm_client.py`（`chat_text`） | ✅ |
| `.env` 自动加载 | `apps/sut/backend/app/settings.py`（`_load_dotenv`） | ✅ |
| 前端页面 | `apps/sut/frontend/src/views/testing/RequirementsView.vue` | ✅ |
| 前端 API 封装 | `apps/sut/frontend/src/api/client.js` | ✅ |
| 后端测试 | `apps/sut/backend/tests/test_requirements.py` | ✅ 10 条 |
| 端到端冒烟 | `scripts/phase1_smoke.py` | ✅ |
| 视觉验证 | `scripts/phase1_visual_check.py` | ✅ 4 张截图 |

## 2. 数据模型

```
platform_requirements
  id / project_id / title / body / status(draft|analyzed|planned) / priority
  source_filename / analysis_json / plan_json / created_at / updated_at

platform_requirement_attachments
  id / requirement_id / filename / content_type / size / stored_path
  extracted_text / extract_note / created_at

platform_requirement_messages
  id / requirement_id / role(user|assistant) / content / created_at
```

`analysis_json` / `plan_json` 存结构化结果，前端直接渲染，不做二次解析。

## 3. 文件提取

零第三方依赖（不引入 pypdf / python-docx）：

| 类型 | 做法 | 失败兜底 |
| --- | --- | --- |
| md / txt / json / csv / yaml / log / html | 依次试 `utf-8-sig` → `utf-8` → `gb18030` | 留 `extract_note` |
| docx | `zipfile` 读 `word/document.xml`，`</w:p>`、`<w:br/>` 转换行后去标签 | 留 note |
| pdf | 正则抓 `stream` 段 + `zlib.decompress`，抽 `( ... )` 文本字面量 | 提示「可能是扫描件或加密，请直接粘贴正文」 |

上传单文件上限 20 MB，超限返回 413；文件落 `data/uploads/requirements/<id>/`。

## 4. 三个 skill

| id | category | 输入 | 输出 |
| --- | --- | --- | --- |
| `requirement.analyze` | requirement | `requirement_id` 或 `text`、`model_id?` | `{summary, features[], ui[], clarifications[], risks[]}`，写库并把状态推 `analyzed` |
| `requirement.plan` | requirement | `requirement_id`、`create_plan?` | `{goal, scope_in[], scope_out[], approach, person_days, milestones[], environments[], test_data[], risks[]}`，可同时建 `TestPlan` |
| `requirement.chat` | requirement | `requirement_id`、`message` | `{reply, analysis_updated, analysis}`，回复里若含 ```json 分析块则吃掉并覆盖库中分析 |

约束：`requirement.plan` 在无分析结果时抛 `SkillError(409, "请先完成需求分析，再生成测试计划")`；`person_days` 用 milestones 的 days 之和校正，避免模型自报不一致。

## 5. HTTP 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET / POST | `/api/platform/requirements` | 列表（`project_id`/`status`/`q` 过滤）/ 新建 |
| GET / PATCH / DELETE | `/api/platform/requirements/{id}` | 详情（含附件与对话）/ 更新 / 删除 |
| POST | `/api/platform/requirements/{id}/attachments` | 上传附件并抽取文本 |
| DELETE | `/api/platform/requirements/{id}/attachments/{aid}` | 删除附件 |
| GET | `/api/platform/requirements/{id}/attachments/{aid}/download` | 下载原文件 |
| POST | `/api/platform/requirements/{id}/analyze` | 触发需求分析 |
| POST | `/api/platform/requirements/{id}/plan` | 触发测试计划 |
| POST | `/api/platform/requirements/{id}/chat` | 对话修订分析 |

## 6. 页面

`/requirements` 两种形态：

- **列表**：hero 指标（需求总数 / 已分析）+ 项目下拉 / 状态筛选 / 搜索 / 刷新 + 表格（ID、标题、项目、状态、优先级、附件数、更新时间、操作）。
- **详情**（`.detail-grid` 三列，对齐目标站）：
  - 左：需求正文（Markdown 原文）+ 附件区（上传 / 删除 / 下载，显示抽取字数与 note）
  - 中：分析 Tabs —— 功能清单 / 界面描述 / 待澄清 / 风险 / 测试计划
  - 右：需求助手聊天（历史消息 + 输入框），回复后自动刷新分析与状态

新建需求走 modal：标题、正文、附件、状态、优先级。

## 7. 与目标站的对齐情况

| 目标站行为 | 本阶段实现 |
| --- | --- |
| 上传 md/txt/pdf/docx | ✅ 四类都支持，且有降级提示 |
| 分析输出功能清单 / 界面描述 / 待澄清项 | ✅ 额外多输出「风险」与「摘要」 |
| 右侧对话改分析 | ✅ `requirement.chat` 支持整体覆盖分析 JSON |
| 测试计划含目标 / 范围 / 人天 | ✅ 另含里程碑、环境、测试数据、风险 |
| 分析结果可直接进用例生成 | ✅ 用例生成仍走 `case.generate`，可传需求正文 |

## 8. 不在本阶段范围

- 需求版本对比、评审流（Phase 5 权限/流程时再补）
- 附件在线预览（当前只做抽取 + 下载）
- 需求与用例的双向追溯矩阵（Phase 5）

## 9. 下一步

Phase 2：功能测试模块——用例管理从「只有列表」升级为可编辑、可评审、可批量写入，并把 `case.generate` 的输入接上 `analysis_json` 的功能清单。
