---
name: shenle-test-plan-generator
enabled: true
description: "需要从需求或接口清单生成测试计划、拆出用例范围与排期时时使用。支持 plan, 用例范围, 优先级, 排期, 风险 相关操作；Use when the task involves plan / 用例范围 / 优先级 / 排期 / 风险.。触发词：cli / record / runner / adapter / skill。"
---

重点：请使用中文沟通！！

# shenle-test-plan-generator — 测试计划生成器

对话式引导生成 AIQE 测试计划 `meta.yaml`：扫描已有编排 → 选 flow → 选环境 → 选策略 → 落盘 → 可选执行。

---

## 🎯 我该怎么用这个技能？

### 一句话理解

你描述想跑哪些编排（或直接给 ID/title），AI 把它们**组合成一个测试计划**（plan），写到 `AI-自动化测试计划/plan-web-{时间戳}-{编排name}/meta.yaml`，然后问你"要不要立刻执行"。

### 典型使用场景

| 你说 | AI 行为 |
|------|---------|
| "生成测试计划" | 列出所有编排让你挑 |
| "把登录相关的编排做一个 plan" | 过滤名称包含"登录"的编排让你挑 |
| "用 c5e7f8a9、d6f8a9b0、4e2c4a40 这三个 flow 做个 plan" | 直接按 ID 选用，无需再次选择 |
| "做一个登录接口的 plan" | 过滤名称含"登录"+"接口"，并优先把 plan 类型推断为 `api` |
| "把 e7f8a9b0 这个编排做一个 plan" | 直接按 ID 选用，类型默认按编排的 task 类型推断 |

### 与其他 Skill 的关系

```
shenle-test-plan-generator  ← 本 Skill（组合 plan）
        │
        │ 读 AI-自动化测试编排/*.yaml      (shenle-test-flow-builder 的产物)
        │ 读 AI-环境变量/{env}/meta.yaml   (环境元信息)
        │ 读 AI-环境变量/{env}/env_var.yaml
        │ 写 AI-自动化测试计划/plan-web-{时间戳}-{编排name}/meta.yaml
        │
        └─→ 可选调用 shenle-test-runner 执行 plan
```

| Skill | 职责 | 与本 Skill 关系 |
|-------|------|----------------|
| shenle-test-flow-builder | 生成单个编排文件 | 本 Skill 的**输入生产者** |
| shenle-test-runner | 执行测试计划 | 本 Skill 的**下游执行者**（可选） |
| 本 Skill | 把若干编排**组合**成一个可执行 plan | — |

---

## 📁 工作空间目录约定

```
{工作空间}/
├── AI-自动化测试编排/                 ← 扫描编排（只读）
│   └── {uuid 或 uuid-with-dashes}.yaml
│
├── AI-环境变量/                       ← 选择 environmentKey（只读）
│   └── {env_name}/
│       ├── meta.yaml
│       └── env_var.yaml
│
├── AI-自动化测试计划/                  ← 落盘目标（写入）
│   └── plan-web-{时间戳}-{编排name}/meta.yaml
│
└── AI-自动化测试执行/                  ← 执行后产生（runner 写入）
    └── 执行记录-YYYYMMDDHHMMSS/
```

> 🔍 **当前工作空间根** = 用户当前操作的目录，默认即 `{cwd}`。如用户切换项目，按用户当前所在项目目录处理。

---

## 🔄 核心流程（6 步）

**MANDATORY — 先读整个文件**：`references/detail.md`（343 行，覆盖「🔄 核心流程（6 步）」的完整细节）。
**不要加载** 其他 references 文件，本任务只需要这一份。

## 🔧 高级能力

### 多 plan 批量生成

用户说"按登录、注册、首页分别生成 plan" → 依次为每个场景生成独立 plan 目录，**不在一个 plan 里塞多个不相关的场景**。

### 追加 / 修改现有 plan

| 用户说 | 行为 |
|--------|------|
| "往 plan-xxx 里加一个 flow" | 读现有 meta.yaml → 在 flows[] 追加 → 重写 |
| "从 plan-xxx 里删掉某个 flow" | 读现有 meta.yaml → 从 flows[] 删除 → 重写 |
| "改 plan-xxx 的环境" | 读现有 meta.yaml → 改 environmentKey → 重写 |
| "改 plan-xxx 的执行策略" | 读现有 meta.yaml → 改 executionStrategy → 重写（注意：本 Skill 默认 serial；用户主动要改才动） |

> 改之前必须先用 `Read` 读现有 meta.yaml，**不要凭记忆改**。

### 复用已有 flow 的 tags

生成 plan 时，**优先沿用 flow 自己的 tags**（从编排 YAML 第 3+ 行读）。除非用户明确说要重写 tags，否则不要覆盖 flow-level tags。

### 类型冲突处理

如果用户同时选了纯 API 的 flow 和 Web UI 的 flow → 自动推断为 `mixed`，并明确告知用户"这两个 flow 类型不同，目录命名为 mixed"。

---

## ⚠️ 关键注意事项

| # | 注意事项 |
|---|----------|
| 1 | **sourceFlowId 保留原始格式**。文件名是 `c5e7f8a9...yaml` 就抄 `c5e7f8a9...`；文件名是 `4e2c4a40-4ee3-45ea-...yaml` 就抄带横线的 UUID。**不要自作主张加/去横线**。 |
| 2 | **顺序敏感**。flows[] 数组顺序 = plan 执行顺序（serial 模式下）。务必按用户给的顺序写入。 |
| 3 | **environmentKey 必须真实存在**。写入前用 `Glob` 验证 `AI-环境变量/{environmentKey}/` 目录存在；不存在则提示用户修正，不要写死。 |
| 4 | **sourceFlowFile 必须真实存在**。写入前用 `Glob` 验证 `AI-自动化测试编排/{sourceFlowFile}` 文件存在；不存在则提示用户修正。 |
| 5 | **created_at 必须单引号包裹**。格式 `YYYY-MM-DD HH:MM:SS`，加单引号避免 YAML 把冒号当 mapping。 |
| 6 | **plan-level tags 可选**。flow-level tags 是必填的（每个 flow 都自带）。plan-level tags 只在用户明确要求时加。 |
| 7 | **执行细节交给 shenle-test-runner**。用户确认执行后，调 `Skill("shenle-test-runner")`，不要自己写 CLI 命令。它会处理 skill 选择等细节。 |
| 8 | **一次只问一条问题**。收集信息时分步问，不轰炸。 |
| 9 | **先预览再写入**。meta.yaml 写盘前必须输出预览并获得确认。 |
| 10 | **YAML 验证不可省**。写盘后必须 `yaml.safe_load()` 验证，失败立即修复。 |
| 11 | **落盘位置默认 `AI-自动化测试计划/`**。用户可指定其他位置，但默认不动。 |
| 12 | **id = 目录名**。`meta.yaml` 的 `id` 字段必须等于父目录名（去掉 `.yaml` 后缀的部分），不要给 ID 起别的名。 |

---

## 📚 参考示例

工作空间里已有的 plan，可参考其 `flows[]` 写法：

- `AI-自动化测试计划/plan-api-login-20260827-150820/meta.yaml` — 历史命名示例（**新生成不再使用**，统一按 `plan-web-{ts}-{name}` 走）
- `AI-自动化测试计划/plan-d6f8a9b0-only-20260908161943/meta.yaml` — 历史命名示例（**新生成不再使用**）
- `AI-自动化测试计划/plan-login-updateinfo-20260909-225754/meta.yaml` — 历史命名示例（**新生成不再使用**）
- `AI-自动化测试计划/4e2c4a404ee345eabac4aede9a44c90f/meta.yaml` — 历史命名示例（**新生成不再使用**）

> 📌 **新生成的 plan 统一命名规则**：`plan-web-{YYYYMMDD-HHMMSS}-{编排name}/`，不再使用 slug 或 type 段。

## 边界与反例

### 不要做（每条都给原因）

- **NEVER** 不要只按接口数量估算工作量——写接口的用例数通常是读接口的 2–3 倍，按数量估会系统性低估
- **NEVER** 不要把“待确认”项留在计划外——未决项不写进计划，最后都会变成上线前的临时加班
- **NEVER** 不要生成没有验收标准的用例——“功能正常”无法判定，执行时只能靠感觉打勾

### 失败与兜底

| 现象 | 处理 |
| --- | --- |
| 需求信息不足 | 先把待澄清项列成清单，不要用假设补全 |
| 用例重复 | 用接口+参数位置+场景三元组去重，重复用例会让覆盖率虚高 |
| 排期过紧 | 砍低优先级场景，不要砍断言 |

### 何时不该用这个 skill

- 只需要读文档或写笔记：走知识库，不要调执行类命令。
- 需要改被测系统的业务数据：先确认数据隔离，再考虑用录制/回放。

## 执行顺序（顺序错了会白跑）

1. 先列范围，再排优先级。
2. 先标未决项，再估工时。
3. 先定验收标准，再写用例。
4. 先评审，再执行。

### 再加一条红线

- **NEVER** 不要把用例数当覆盖率——数量多但都在同一维度，覆盖仍然是空的

### 兜底原则

任何一步失败，先留证（截图、响应体、日志），再重试；没有证据的重跑只会把问题变成偶发。
