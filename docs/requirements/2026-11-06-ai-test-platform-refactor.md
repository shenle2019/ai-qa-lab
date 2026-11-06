# ai-qa-lab → Raina 版 AI 测试平台 重构方案

> 目标参照：微信公众号「Raina测试」文章《终于把 AI测试平台搭建起来了》（2026-11-02）
> 原文链接：https://mp.weixin.qq.com/s/6TN-sNtRTGy1G5Ht__h9mA
> 本地存档：`C:\Users\Administrator\一人公司\DeepSeekharness\wechat-article\终于把_AI测试平台搭建起来了\`（含 33 张 UI 截图）
> 记录日期：2026-11-06
> 决策：框架对齐目标站，能力可扩展，细节逐步对齐。

---

## 1. 目标站（Raina 版）的产品结构

### 1.1 侧边栏（从截图还原）

```
工作台
├── 项目管理
├── 系统 AI 配置
├── AI 调用日志
└── 用户管理

当前项目
└── 概览

测试
├── 需求管理
├── 功能测试
└── 知识库

自动化
├── 环境管理
├── 接口自动化
└── UI 自动化

项目
├── 模块管理
└── 成员管理
```

### 1.2 七大核心模块（文章正文）

| # | 模块 | 能力 |
|---|---|---|
| 1 | **需求管理** | 上传 md/txt/pdf/docx；需求分析（功能清单/界面描述/待澄清项）；右侧对话 Agent 改分析；测试计划（目标/范围/人天估算） |
| 2 | **功能测试** | AI 生成用例（先生成草稿，用户决定是否写入用例管理）；用例管理 |
| 3 | **知识库** | 创建知识库、文档上传、分块、试检索；供 AI 用例生成等 Agent 检索 |
| 4 | **接口自动化** | 接口资产（导入 OpenAPI/Swagger）→ 接口清单 → 一键导入接口管理；接口管理（类 Postman 调试）；单接口 Agent（单接口用例设计）；场景 Agent（多接口串联、数据流、详细请求）；编排页（+编排 Agent）；执行 + 失败 AI 归因 |
| 5 | **UI 自动化** | 功能测试用例执行；探索生成脚本 / Agent 直跑；midscene 图片识别；环境变量注入（localStorage，免登录）；自由对话探索 |
| 6 | **项目管理** | 项目为关键载体，需求/用例/接口/UI 用例都围绕项目 |
| 7 | **系统 AI 配置** | 大模型管理（Agent 基础模型，建议多模态）；向量模型管理（知识库用）；Midscene（UI 自动化视觉模型，需多模态） |

### 1.3 页面级 UI 特征（截图观察）

- 顶栏：品牌名 + 环境切换（RainaTest）+ 右侧 `Admin 修改密码 退出`。
- 左侧分组导航（见 1.1），分组标题灰字小写，当前项高亮蓝底。
- 内容区：页内 Tab（如 接口管理页的 `场景Agent / 单接口Agent / 接口资产 / 接口管理 / 单接口用例 / 接口场景 / 执行记录`）。
- 表格：方法用彩色标签（GET 蓝 / POST 绿 / PATCH 橙 / DELETE 红），操作列 `编辑/调试/删除`。
- 弹窗：新建需求等居中 Modal，带 `取消/确定`。
- 分页：`共 N 条  < 1 >  20/页`。

---

## 2. ai-qa-lab 现状

- 技术栈：FastAPI + SQLAlchemy + SQLite；前端 Vue3 + Vite（`apps/sut` 同时承载 SUT 与平台 UI，`/ui/`）。
- 现有后端：`platform_api.py`（492 行）、`model_api.py`、`case_generator.py`、`case_executor.py`、`kb.py`、`llm_client.py`。
- 现有前端视图（12 个）：Dashboard / Tickets / Workbench / Knowledge / Platform / Models / TestCases / Methodology / Report / Portfolio / Login / NotFound。
- 现有侧栏是**扁平 10 项**（仪表盘、工单、API 工作台、知识库、测试平台、模型中心、测试用例、方法论、项目报告、模块验收），与目标站的**分组 5 段**结构不一致。
- 已具备：项目/用例/计划/执行/缺陷、AI 生成用例草稿、审核门、真实执行、HTML 报告、模型中心（OpenAI 兼容）。

---

## 3. 差距（现状 → 目标）

| 目标模块 | 现状 | 差距 |
|---|---|---|
| 工作台·项目管理 | 有（Platform.vue 内） | 需独立成页 + 项目详情/编辑/归档 |
| 工作台·系统 AI 配置 | 有 Models.vue（模型中心） | 需拆成 大模型 / 向量模型 / Midscene 三个 Tab |
| 工作台·AI 调用日志 | 无 | 新建（llm_calls 表已有基础） |
| 工作台·用户管理 | 无 | 新建（单用户可先占位） |
| 当前项目·概览 | 无 | 新建（按项目聚合） |
| 测试·需求管理 | 无 | 新建（上传/解析/需求分析/对话Agent/测试计划） |
| 测试·功能测试 | 部分（用例生成+审核门） | 拆成 AI生成用例 / 用例管理 |
| 测试·知识库 | 有（Knowledge.vue 是问答，非知识库管理） | 重做：知识库/文档/分块/检索 |
| 自动化·环境管理 | 无 | 新建 |
| 自动化·接口自动化 | 有半成品（Workbench 前端 localStorage） | 拆成 资产/管理/单接口Agent/场景Agent/执行记录 6 个 Tab |
| 自动化·UI 自动化 | 只有 miniplaywright 库，无平台入口 | 新建：用例/套件/执行记录 + 探索生成/Agent直跑 |
| 项目·模块管理 | 无 | 新建 |
| 项目·成员管理 | 无 | 新建（可先占位） |

---

## 4. 扩展机制（「所有测试能力可扩展」怎么落地）

核心思路：**能力 = Skill（可注册的执行单元）**，页面只负责调用，不硬编码具体能力。

### 4.1 Skill 注册表（后端）

```python
# app/skills/registry.py
@dataclass
class Skill:
    id: str                 # 唯一标识，如 "req.analyze"
    name: str               # 显示名
    category: str           # requirement | case | api | ui | kb | report
    input_schema: dict      # JSON Schema
    output_schema: dict
    handler: Callable       # 执行入口
    version: str = "0.1.0"
    enabled: bool = True

REGISTRY: dict[str, Skill] = {}

def register(skill: Skill) -> None: ...
def get(skill_id: str) -> Skill: ...
def list_skills(category: str | None = None) -> list[Skill]: ...
```

- 内置 Skill 放 `app/skills/builtin/`，每个文件一个能力（`req_analyze.py`、`case_generate.py`、`api_single_agent.py`、`ui_explore.py`…）。
- 外部 Skill 放 `app/skills/external/`，从 GitHub / skill 官网拉取后适配成同一接口。
- 统一 HTTP 入口：`POST /platform/skills/{skill_id}/run`，body = 输入 JSON，返回 = 输出 JSON。

### 4.2 前端能力注册（可配置）

- 每个页面（需求管理/功能测试/接口自动化/UI自动化）通过 `GET /platform/skills?category=xxx` 拉取可用能力，渲染按钮/菜单。
- 新增一个 Skill，前端零改动即可出现（按钮名来自 `skill.name`）。

### 4.3 页面骨架与能力解耦

- 页面负责：列表、表单、Tab、结果展示、草稿/审核/写入流程。
- Skill 负责：真正调 LLM / 执行测试 / 解析文件。
- 这样「细节慢慢对齐」时，只换 Skill 实现，不动页面。

---

## 5. 缺失 Skill 的获取清单

| 能力 | 现状 | 去哪里找 | 备注 |
|---|---|---|---|
| 需求分析（功能清单/界面描述/待澄清项） | 无 | GitHub `test-requirement-analysis`、skill 市场 | 先自研 prompt 版，再找现成 |
| 测试计划生成 | 无 | 同上 | 自研 prompt 版 |
| 测试用例生成 | 有（case_generator.py） | 可复用，抽象成 Skill | 转为注册表 |
| 接口用例生成（单接口） | 无 | GitHub `api-test-case-generation` | prompt + 接口 schema |
| 接口场景编排 | 无 | GitHub `api-scenario-*` | 数据流图 + 请求链 |
| UI 探索生成脚本 | 无 | midscene / `playwright` codegen | 先接 miniplaywright |
| 失败 AI 归因 | 无 | 自研 prompt | 执行日志 + 断言差异 |
| 文件解析（pdf/docx/md） | 无 | `markitdown` / `python-docx` / `pypdf` | 已装 python-docx；pdf 用 pypdf |
| 知识库切分/向量化 | 有 `kb.py` 基础 | 复用 | 抽象成 Skill |

获取方式：
1. 先用 `find-skills` 技能在本地 skill 目录/市场里找；
2. 找不到再去 GitHub 搜 star 高的实现，记录项目/star/许可证/选型理由（遵循 CLAUDE.md 的模块复刻规则）；
3. 统一适配成 §4.1 的 Skill 接口，放 `app/skills/external/`。

---

## 6. 分阶段路线图

### Phase 0（本次先做）：框架对齐 + 可扩展骨架
- [ ] 侧栏重构为目标的 5 段分组（工作台/当前项目/测试/自动化/项目）。
- [ ] 新增路由与占位页：项目管理、系统AI配置、AI调用日志、用户管理、项目概览、需求管理、功能测试、知识库、环境管理、接口自动化、UI自动化、模块管理、成员管理。
- [ ] 后端加 `skills/registry.py` + `GET /platform/skills` + `POST /platform/skills/{id}/run`。
- [ ] 把现有「AI 生成用例」和「用例管理」注册成第一批 Skill。
- [ ] 保证现有功能不回归（旧路由保留或重定向）。

### Phase 1：需求管理闭环
- 需求上传（md/txt/pdf/docx）→ 需求分析（功能清单/界面描述/待澄清项）→ 右侧对话 Agent 修改 → 测试计划生成。

### Phase 2：接口自动化闭环
- 接口资产导入（OpenAPI）→ 接口管理（调试）→ 单接口 Agent → 场景 Agent → 编排 → 执行 → AI 归因。

### Phase 3：知识库 + 功能测试
- 知识库/文档/分块/试检索 → 供用例生成检索；AI 生成用例草稿 → 审核 → 写入。

### Phase 4：UI 自动化 + 环境管理
- UI 用例/套件/执行记录；探索生成脚本 / Agent 直跑；环境变量注入。

### Phase 5：系统 AI 配置 + 日志 + 用户/模块/成员
- 大模型/向量模型/Midscene 三 Tab；AI 调用日志；项目下的模块与成员。

---

## 7. 验收标准（每个 Phase）
- 页面能点开、无报错；
- 至少一条真实链路（输入→Skill 执行→结果落库→页面可见）；
- 不破坏现有 196 条测试用例与报告页；
- 新增能力必须能在 `GET /platform/skills` 里看到，并可通过 `POST /platform/skills/{id}/run` 调用。
