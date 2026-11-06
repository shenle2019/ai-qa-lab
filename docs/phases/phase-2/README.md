# Phase 2 · 功能测试（用例管理 + AI 生成）

> 目标：把「功能测试」从只能生成、只能看，做成一个真正能用的用例工作台 —— 能改、能批量流转、能从需求库带着分析结果生成。
>
> 对标目标站：需求上传后的「AI 生成用例（草稿）→ 使用者决定是否写入用例管理」这条链路。

## 1. 交付清单

| 层 | 交付物 | 说明 |
| --- | --- | --- |
| Skill | `case.update` | 编辑用例的标题 / 模块 / 优先级 / 步骤 / 预期结果 |
| Skill | `case.batch` | 批量提交审核 / 通过 / 驳回 / 退回草稿 / 删除，逐条返回跳过原因 |
| Skill | `case.generate`（增强） | 支持 `requirement_id`，自动拼上需求分析出来的功能点 |
| REST | `POST /api/platform/cases/batch` | 批量流转入口 |
| REST | `GET /api/platform/cases/{id}` | 单条详情（含 steps / expected / steps_json） |
| REST | `PATCH /api/platform/cases/{id}` | 编辑，转发给 `case.update` |
| REST | `DELETE /api/platform/cases/{id}` | 删除，返回 204 |
| 前端 | `views/testing/FunctionalView.vue` | 双 Tab：用例管理（表格 + 复选 + 批量栏 + 编辑弹窗）/ AI 生成（表单 + 本次生成预览） |
| 测试 | `tests/test_case_management.py` | 8 条，覆盖编辑、批量流、跳过、删除、从分析生成、skill 注册 |

## 2. 用例状态机

```
draft ──submit_review──> pending_review ──approve──> approved
                              │
                              └──reject──> rejected
   ↑                                        │
   └────────── draft（退回草稿）─────────────┘
```

`case.batch` 的每条动作都先校验当前状态，不合法的进 `skipped`，不会因为一条错就整批失败。`approve` / `reject` 同时写一条 `CaseReview`，评审记录可追溯。

## 3. Skill 契约

### `case.update`

- **入参**：`{case_id: int, title?, module?, priority?, steps?, expected?}`
- **出参**：`{case: CaseOut, changed: ["title", ...]}`
- **错误**：无字段 → 400「没有需要修改的字段」；标题空白 → 400「标题不能为空」；优先级不在 `low/medium/high` → 400；用例不存在 → 404。

### `case.batch`

- **入参**：`{action: "submit_review"|"approve"|"reject"|"draft"|"delete", ids: [int], reviewer?, comment?}`
- **出参**：`{action, updated: int, skipped: [{id, reason}]}`
- **跳过原因**：`用例不存在` / `状态 approved 不能执行 submit_review` 之类。

### `case.generate`（增强）

- **入参**：`{project_id?, requirement_id?, requirement?, max_cases?}`
- 传 `requirement_id` 时，正文取 `requirement.body or requirement.title`；如果这条需求已经分析过，会把 `analysis_json.features` 里的功能点和验收标准一起塞进 prompt，让模型逐条覆盖。
- **出参**：`{model_name, prompt_version, cases: [{id, project_id, title, module, priority, steps, expected, status, source}]}`，状态一律 `draft`。

## 4. 前端页面

**用例管理 Tab**

- 工具条：项目下拉、状态下拉、关键词搜索、刷新。
- 表格列：复选 / ID / 标题 / 模块 / 优先级 / 状态徽章 / 来源（AI 或手工）/ 操作（编辑、删除）。
- 勾选后出现批量栏：`已选 N` + 提交审核 / 通过 / 驳回 / 退回草稿 / 删除。
- 编辑弹窗：进弹窗先用列表数据占位，再拉 `GET /cases/{id}` 补全步骤和预期结果（列表接口不返回这两列，避免列表变重）。

**AI 生成 Tab**

- 左侧表单：项目、从需求库选择（自动带上分析出的功能点）、需求文本、最多生成条数。
- 右侧「本次生成」：每条草稿一张卡片，显示标题、模块、优先级、步骤、预期结果，顶部有「全部提交审核」。
- 生成成功后有提示条：`已生成 N 条草稿（模型 xxx），确认后可提交审核`。

## 5. 与目标站对齐

| 目标站能力 | 本阶段状态 |
| --- | --- |
| AI 生成用例，先草稿再由人决定是否入库 | ✅ 生成即 `draft`，可批量提交审核 |
| 用例列表、按项目 / 状态筛选 | ✅ |
| 用例编辑 | ✅ 弹窗编辑，走 `case.update` |
| 用例评审（通过 / 驳回） | ✅ 批量流转 + 评审记录 |
| 用例删除 | ✅ 单条 + 批量 |
| 从需求直接生成 | ✅ 关联需求库，自动带功能点 |

## 6. 下一步（Phase 3 知识库）

- 用例数量起来以后，靠关键词搜索不够用了，Phase 3 做知识库：建库、上传、分块、试检索。
- 生成用例时把知识库里检索到的片段作为上下文，减少「凭空造接口」。
