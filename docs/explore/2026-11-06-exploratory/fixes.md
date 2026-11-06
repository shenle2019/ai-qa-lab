# 探索式测试问题修复记录（2026-11-06）

对应清单：`docs/explore/2026-11-06-exploratory/findings.md`（16 条）。
复验脚本：`scripts/explore_pass5.py` → 19/19 通过，结果写 `pass5.json`，截图同目录 `shots/after-*.png`。

| # | 问题 | 修改 | 复验 |
| --- | --- | --- | --- |
| 1 | 新建需求空标题点确定无提示 | `RequirementsView.vue`：弹窗内加 `modal-alert` 错误块；`FunctionalView` / `UsersView` / `KnowledgeBaseView` / `ModulesView` / `MembersView` / `EnvironmentsView` 同步 | `modal-error-visible`：弹窗内 `.alert.error` = 1 |
| 2 | 概览「执行记录 2 / 通过率 75%」矛盾 | 后端 `SummaryOut` 增加 `results_passed/results_failed/results_total`；前端把口径写成「按用例结果统计 · 3 通过 / 1 失败」，执行记录改「全平台累计执行次数」，hero 改「全平台聚合视角」 | `overview-no-dash`、`overview-passrate-label` |
| 3 | 10 个旧页与新版同名并存 | `App.vue`：分组改名「旧版页面（V1）」，10 条链接统一 `↩` 图标 + `nav-legacy` 淡化，文字保留但样式区分 | `legacy-labelled`：summary=旧版页面（V1），10 条 |
| 4 | 404 页「返回仪表盘」指向旧版 | `NotFound.vue`：主按钮「返回项目概览」→ `/overview`，次按钮「打开项目管理」，并加导航提示 | `404-target`：按钮=返回项目概览，落 `/overview` |
| 5 | 环境管理只有「规划中」+ 过期 Phase + 假 skill 名 | 新增 `environment_models.py`（`environments` 表）、`environment_api.py`（GET/POST/PATCH/DELETE `/api/platform/environments`）、`EnvironmentsView.vue` 全量重写（项目下拉 + 新建 + 列表 + 编辑弹窗 + 变量 JSON 校验） | `environments-real`：无占位文案，表单存在 |
| 6 | 弹窗 Esc 关不掉 | `App.vue` 全局 `keydown` → 关闭最上层 `.modal-mask`（优先 `[data-modal-close]`，否则文字为 关闭/取消/返回列表 的按钮，再退化到点遮罩）；各弹窗补 `data-modal-close` | `esc-closes-modal`：Esc 后弹窗数 0 |
| 7 | 键盘焦点环深黑色不可见 | `style-fixes.css`：`:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }` | `focus-ring`：`rgb(56,189,248)` 2px |
| 8 | 「刷新状态」含义不明、零反馈 | 文案改「检测服务」，反馈带时间戳并保留 4s（`服务正常 · 16:20:35`） | `health-feedback` |
| 9 | 单接口 Agent 未选接口仍可点 | 按钮 `:disabled="singleBusy \|\| !singleForm.endpoint_id"` + 提示「先在上方选择接口」 | `single-agent-disabled` |
| 10 | 模块/成员默认落空项目 | 新增 `utils/project.js`：统一 key `aiqa.project`（兼容各页旧 key），`pickProjectSmart` 在没有记忆时选**用例最多**的项目；模块/成员/环境页接入，接口/UI 自动化同步读写同一 key | `shared-project`（记忆=2）、`busy-default`（无记忆也落 2） |
| 11 | 调试抽屉 Base URL 空白无提示 | placeholder 改「留空则用接口资产地址，例如 http://127.0.0.1:8000」 | `debug-baseurl-hint` |
| 12 | 200 字搜索词不截断 | 需求/功能测试/接口管理搜索框 `maxlength="80"`，placeholder 注明上限 | `search-maxlength`：80 |
| 13 | 480px 侧栏吃满首屏 | `style-fixes.css`：≤900px 侧栏变抽屉（`position:fixed` + `translateX(-100%)`），顶栏加 `☰` 开关，`.menu-open` 展开；内容区留出全宽 | `narrow-drawer`：toggle 可见 / 默认隐藏 / 点击展开 |
| 14 | 附件原生亮色按钮、下拉偏浅 | `body input[type='file']` 及 `::file-selector-button` 统一深色；`select` 全局补自绘 chevron（组件 `background` 简写会覆盖，故用 `!important` 只在样式层断言） | `file-input-themed` |
| 15 | 「API 文档」在关闭 docs 时 404 | `/health` 增加 `docs` 字段；`App.vue` 依据 `docs` 决定是否渲染入口（本地仍显示） | `docs-link` 仅在可用时出现 |
| 16 | 图标复用 | 13 个新页面图标全部唯一（◫ ◍ ◷ ☺ ◉ ▤ ☑ ✦ ⚙ ⌁ ▣ ▦ ⚇），旧版统一 `↩` | `icons-unique`：13 个无重复 |

## 顺带修的两处

- **UI 自动化的运行环境可见性**：`/health` 增加 `ui_automation`（playwright + chromium 是否存在）；`UiAutomationView` 在缺失时顶部提示，避免用户以为按钮坏了。生产镜像不装浏览器（体积/构建风险），本地为 true。
- **生产依赖补齐**：`requirements.txt` 之前只列 5 个包，但代码已依赖 `python-dotenv`、`python-multipart`、`PyYAML`，Docker 构建会直接崩。已按本地版本锁定。

## 复验命令

```powershell
python scripts\explore_pass5.py        # 19/19
.venv\Scripts\python.exe -m pytest apps/sut/backend/tests -q   # 142 passed
```
