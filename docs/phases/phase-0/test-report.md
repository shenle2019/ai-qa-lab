# Phase 0 · 测试报告

> 版本：Phase 0（骨架与可扩展底座）
> 结论：**通过**。后端注册表与接口可用，前端 5 组侧栏与新路由全部渲染，AI 生成链路端到端打通；占位页面按计划留给 Phase 1–5。

## 1. 质量指标

| 指标 | 数值 |
| --- | --- |
| 后端单测（本阶段新增） | 8 条，8 通过 |
| 后端单测（全量） | 72 条，72 通过 |
| 失败 / 跳过 | 0 / 0 |
| 新接口冒烟 | 4 项，4 通过 |
| 新页面渲染 | 6 个页面截图核对，全部正常 |
| 前端构建 | 成功（Vite，7.1 s） |
| JS 运行时报错 | 0（Playwright `pageerror` 监听为空） |

## 2. 验收标准对照

| 验收项 | 标准 | 实测 | 结论 |
| --- | --- | --- | --- |
| 侧栏结构 | 与目标站一致的 5 组 + 开发工具 | 工作台 / 当前项目 / 测试 / 自动化 / 项目 + 折叠开发工具 | ✅ |
| 侧栏可达性 | 1440×900 下 13 项全部可见 | 全部可见（`phase0-sidebar.txt`） | ✅ |
| 新页面可访问 | 13 个路由均能打开 | 6 个截图 + 其余路由构建通过 | ✅ |
| 旧页面不回归 | 原 10 个页面仍可访问 | 路由全部保留 | ✅ |
| Skill 可注册 | 新增 skill 不改前端即可出现 | 概览页按 `category` 自动列出 3 条 | ✅ |
| Skill 可执行 | `POST .../run` 返回业务结果 | `project.list` / `case.list` / `case.generate` 均成功 | ✅ |
| 错误处理 | 未知 skill / 缺参有明确错误 | 404 / 400，中文提示 | ✅ |
| AI 生成 | 输入需求产出 draft 用例 | 5 条 draft，prompt 版本记录 | ✅ |

## 3. 风险与缓解

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| `.env` 未自动加载 | 重启后 AI 生成报「未配置 API Key」 | Phase 1 在 settings 启动时 `load_dotenv`，并加启动自检日志 |
| 占位页面较多 | 用户点进去只看到规划 | 每个占位页标注 Phase 编号 + 能力清单，避免「看起来坏了」 |
| 侧栏 13 项在小屏溢出 | 1000px 以下出现滚动 | `.nav` 已设 `overflow-y:auto`；Phase 5 做响应式抽屉 |
| 用例标题中文在控制台乱码 | 仅影响 PowerShell 查看 | 数据与前端正常；文档已注明 |

## 4. 遗留事项（移交后续 Phase）

1. Phase 1：需求上传（md/txt/pdf/docx）、AI 分析（功能清单 / 界面描述 / 待澄清项）、右侧对话 Agent、测试计划生成。
2. Phase 2：功能测试页补「写入用例管理 / 提交评审 / 批量操作」，修表格列宽。
3. Phase 3：知识库（建库 / 上传 / 分块 / 试检索）、接口资产导入与调试、单接口 / 场景 Agent。
4. Phase 4：环境管理、UI 自动化（探索生成 / Agent 直跑 / midscene / localStorage 注入）。
5. Phase 5：模块 / 成员 / 用户、权限与审计、响应式与视觉细节打磨。

## 5. 附件

- 设计文档：`docs/phases/phase-0/README.md`
- 测试记录：`docs/phases/phase-0/test-record.md`
- 截图：`docs/screenshots/phase0-*.png`
- 测试代码：`apps/sut/backend/tests/test_skills_registry.py`
- 冒烟脚本：`scripts/phase0_visual_check.py`
