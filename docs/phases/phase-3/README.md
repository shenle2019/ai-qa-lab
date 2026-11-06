# Phase 3 · 知识库

> 目标：给平台一个项目级的资料底座 —— 文档进来能自动切块，问题进来能检索到具体片段，生成类 Agent 可以引用它而不是凭空发挥。

## 1. 交付清单

| 层 | 交付物 | 说明 |
| --- | --- | --- |
| 数据 | `knowledge_bases` | 知识库：名称、所属项目、分块大小、重叠字符 |
| 数据 | `knowledge_documents` | 文档：文件名、来源、字符数、分块数、提取备注 |
| 数据 | `knowledge_chunks` | 分块：序号、正文、字符数 |
| 逻辑 | `knowledge_chunker.py` | 先按空行切段，再按 `chunk_size` 装箱，带 `chunk_overlap` 重叠 |
| 逻辑 | `knowledge_search.py` | 词面向量：中文二元组 + 英文词 + 原句命中加成，按相关度排序 |
| REST | 知识库 CRUD | `GET/POST/PATCH/DELETE /api/platform/knowledge-bases` |
| REST | 文档 | 列表、上传（multipart）、粘贴文本、删除、分块查看 |
| REST | 检索 | `POST /api/platform/knowledge-bases/{id}/search` |
| Skill | `kb.create` / `kb.list` / `kb.search` / `kb.document.add` | 能力照样走注册表，页面只调用 |
| 前端 | `views/testing/KnowledgeBaseView.vue` | 左库列表 + 右文档表 + 试检索 + 分块查看弹窗 |
| 测试 | `tests/test_knowledge.py` | 11 条，见测试记录 |

## 2. 分块策略

1. 统一换行、去掉行尾空白。
2. 按空行切段（`\n\s*\n+`）。
3. 逐段装箱：能塞进当前缓冲区就塞，塞不下先把缓冲区落盘，再把上一块尾部 `chunk_overlap` 个字符带进下一块。
4. 单段超过 `chunk_size` 时直接硬切，保证没有超长块。

这样切的好处是可解释：每个块的边界要么是段落边界，要么是固定窗口，出问题时能一眼看出是分块参数不对还是文档本身没有结构。

默认 `chunk_size=600` / `chunk_overlap=100`，建库时可以改。改完只影响之后入库的文档，不会重切历史数据。

## 3. 检索策略

当前是**词面检索**，不是向量检索：

- 中文按二元组切（「导出接口」→ 导出/出接/接口），英文和数字按词切；
- 命中词数 / 查询词数 作为相关度，原句整段命中额外 +5；
- 返回 `chunk_id / document_id / filename / seq / score / snippet`，按分数倒序。

为什么先不做向量：目标站的向量检索依赖「向量模型管理」，那属于 Phase 5 的系统 AI 配置。词面检索在接口文档这种术语密集的场景已经够用（见测试记录里的真实命中），而且接口形状不变，Phase 5 换实现时页面不用动。

## 4. Skill 契约

### `kb.search`

- **入参**：`{kb_id: int, query: str, top_k?: int = 5}`
- **出参**：`{kb_id, query, total, hits: [...], context: "[文件#序号] 片段\n\n..."}`
- `context` 是给 prompt 直接用的拼装结果，生成类 skill 以后直接把它塞进 system prompt 即可。
- **错误**：`kb_id` 或 `query` 为空 → 400；知识库不存在 → 404。

### `kb.document.add`

- **入参**：`{kb_id: int, filename?: str, text: str}`
- **出参**：`{document: {id, kb_id, filename, chunk_count, char_count}}`

### `kb.create` / `kb.list`

建库和列库，`kb.list` 会带上 `document_count` 与 `chunk_count`，页面直接渲染，不需要再发两个统计请求。

## 5. 页面

- **左栏**：知识库列表，显示文档数/分块数，可删除；「新建知识库」弹窗可设分块参数。
- **右栏上**：文档表（文件名 / 来源 / 字符 / 分块 / 时间 / 操作），支持上传文件与粘贴文本；「分块」按钮打开分块查看弹窗。
- **右栏下**：试检索。输入问题、选 top_k，结果按相关度倒序，带分数条与片段；用来判断文档切得好不好。
- 顶部三个指标：知识库数 / 文档数 / 分块数。

## 6. 与目标站对齐

| 目标站能力 | 本阶段状态 |
| --- | --- |
| 新建知识库 | ✅ 可设分块大小与重叠 |
| 上传文档自动分块 | ✅ md/txt/docx/pdf，≤20MB |
| 分块查看 | ✅ 弹窗按序号列表 |
| 试检索（看命中片段与相似度） | ✅ 词面检索 + 分数条 + 耗时 |
| 被用例生成 / 需求分析引用 | ⏳ 接口已备好（`kb.search` 返回 `context`），Phase 4 接进生成链路 |
| 向量检索 | ⏳ 等 Phase 5 的向量模型管理 |

## 7. 下一步（Phase 4 接口自动化）

- 接口资产：导入 OpenAPI/Swagger，落到接口表。
- 接口管理：类 Postman 的调试面板。
- 单接口 Agent / 场景 Agent：生成用例，场景 Agent 负责多接口串联和数据流转。
- 知识库会在这一步真正被用起来：生成接口用例前先检索接口约定。
