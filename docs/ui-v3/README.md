# UI/UX 改造记录（uizze-ui · 2026-11-06）

本次改造按 `uizze-ui` skill 的 **Build the UI** 流程执行（不依赖账号的那一半）。

## 一、先说清楚的前提

`uizze-ui` 的完整工作流是 image-first：先有一张目标界面图，再 1:1 实现，最后渲染比对。
`references/workflow.md` 对这一条有明确约束：

> If image generation is unavailable … state the limitation and build directly from the brief and
> existing UI/UX conventions. Do not fabricate a generated image or claim a 1:1 match without a
> real target.

本次会话**没有图像生成工具**，也**没有连接 Uizze MCP**（`https://uizze.com/mcp` 需要付费账号）。
所以：没有目标图、没有做像素级 1:1 比对。改造是依据现有设计令牌、数据契约和页面结构做的一轮
系统化梳理，不是「照图复刻」。这一点在交付说明里同样写明，不当作 Uizze 产物。

## 二、诊断：改之前到底哪里不对

改了 13 个页面、20 多个组件后，共同的问题收敛成六条：

1. **标题重复两次**。`App.vue` 的 topbar 渲染 `<h1>{{ 页面标题 }}</h1>`，每个视图的 `.hero` 里又渲染一次同名标题，同一屏出现两个「功能测试」。
2. **卡片全是渐变 + 径向光斑**。每个 `.card`、`.stat-card` 都带 `radial-gradient` 光斑和悬浮阴影，12 个卡片排在一起时层级完全扁平，看不出主次。
3. **字阶失控**。同一屏同时存在 10.5 / 12 / 13.5 / 16 / 28 / 34px 六级字号，且没有 token，改一处要翻三个文件。
4. **表格可读性差**。没有吸顶表头，滚动时列名消失；没有斑马纹；数字用比例字体，`3`、`7`、`11` 宽度不一致导致列边参差。
5. **按钮全是一个色**。主按钮、次按钮、危险按钮都是高亮青，`删除` 和 `保存` 看着一样重。
6. **缺状态**。列表在没有数据时和加载中时长得一样，用户分不清「还没加载完」和「确实没有」。

## 三、改了什么

### 3.1 设计令牌（新建 `src/theme.css`）

在 `style.css`、`style-fixes.css` 之后引入，用一层叠加的方式接管视觉，不动组件结构：

| 类别 | 变量 | 用途 |
| --- | --- | --- |
| 字号 | `--fs-2xs` … `--fs-3xl` | 10 → 30px 六档，全站只用这六档 |
| 间距 | `--sp-1` … `--sp-8` | 4 → 40px，取代散落的 `padding: 13px 17px` |
| 描边 | `--hairline` / `--hairline-strong` | 1px 分隔线，替代阴影分层 |
| 圆角 | `--radius-sm/md/lg` | 6 / 10 / 14px |
| 语义色 | `--ok` / `--warn` / `--danger` + soft 变体 | 通过、待审、失败 |
| 数字 | `--font-mono` | 计数、耗时、状态码 |

### 3.2 标题只出现一次（`App.vue`）

新增 `heroOwnsTitle`：挂载和路由变化后探测 `.content .hero h1, .content .hero h2`，
命中就把 topbar 的大标题降级为面包屑 `AI 测试平台 · 质量工程工作台`，否则保留原标题。
这样 13 个视图不用逐个改模板，标题也不会重复。

### 3.3 层级：从「卡片堆」变成「页面骨架」

- `.hero` 从卡片改为页面头：去掉边框和底色，只留一条底部发丝线，标题 30px / `-0.025em`，描述限制 66ch，指标右对齐。
- `.card` 改纯色 `--panel-flat` + 1px 描边，删除所有径向光斑。
- 统计卡改左侧 3px 色条 + 等宽数字，代替「大渐变块」。
- `.topbar` 吸顶 + 毛玻璃 + 1px 下边线。

### 3.4 表格

- 表头 `position: sticky`，滚动时钉住。
- 斑马纹 `tbody tr:nth-child(even)`。
- `font-variant-numeric: tabular-nums`，数字列对齐。
- 表头 `white-space: nowrap`，避免「模 块」「来 源」被拆成两行。
- `.row-actions` 强制单行，编辑/删除不再上下堆叠。

### 3.5 按钮与状态

- 按钮改扁平：默认实心青、`ghost` 描边、`danger` 红描边，hover 只换色不下沉。
- `:focus-visible` 统一 2px `--accent` outline + 2px offset，键盘可达。
- badge 按语义配色：`pending/open` 黄、`running` 蓝、`approved/passed/closed` 绿、`draft/rejected/failed` 红。
- tabs 从药丸改为下划线，和表格/内容区分开。
- 空态 `.empty` 改虚线框 + 更大留白；新增 `.skeleton` 扫光动画与 `.alert.ok/.alert.info`。

### 3.6 响应式

- `≤1200px`：统计卡 2 列，表格内边距收紧、字号降到 12.5px。
- `≤900px`：侧栏变抽屉（`translateX(-100%)`，☰ 打开），topbar 收成单行、隐藏面包屑，hero 单列。
- `prefers-reduced-motion` 下关闭所有过渡与入场动画。

### 3.7 顺带修的一个功能缺口

知识库涨到 24 个之后，左栏是一长条没有检索的列表。加了 `.kb-filter` 搜索框
（按名称/描述过滤），标题右侧显示 `2 / 24 个`，并区分「还没有知识库」与「没有匹配『数据』的知识库」两种空态。

## 四、验证

| 项 | 结果 |
| --- | --- |
| 前端构建 | `✓ built in 6.8–7.2s`，无 error |
| 后端回归 | `pytest apps/sut/backend/tests -q` → **142 passed** |
| 桌面截图 | 13 个页面，`docs/ui-v3/v3-*.png` |
| 窄屏截图 | 1024px（`v3-narrow-1024.png`）、480px（`v3-narrow-overview.png`） |
| console / pageerror | 13 个页面均为 **0** |
| 横向溢出 | 1024px、480px 均为 **0** |
| 焦点环 | `:focus-visible` → `rgb(56, 189, 248)` 2px |
| 知识库过滤 | 输入「数据」→ 2 / 24 条 |

## 五、已知限制

1. **没有目标图**，所以不是 1:1 复刻（见第一节）。
2. 1024px 下 `来源` 列仍会把「手工」折成两行——列宽由内容比例决定，在没有改表格 DOM 的前提下无法既保标题换行又保窄列不换行。
3. loading 态只补了 `.skeleton` 样式与 `.alert` 语义，**没有逐页接入**：多数页面在首次请求期间仍显示空态而不是骨架屏。
4. 工作台之外的 10 个旧版页面（`/dashboard` 等）沿用旧样式，只做了令牌继承，没有重新设计。
