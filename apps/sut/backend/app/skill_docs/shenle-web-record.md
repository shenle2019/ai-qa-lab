---
name: shenle-web-record
description: "需要在真实浏览器里录制操作步骤并导出可回放的脚本时时使用。支持 record, 录制, SNAP, 回放, 步骤 相关操作；Use when the task involves record / 录制 / SNAP / 回放 / 步骤."
---

# shenle-web-record

这是一个**驱动类技能**：把本地 `shenle-web-record` 这个 Python CLI 包成对话式的工作流。

底层 CLI 位于 `apps/shenle-web-record/`，调用方式：

```
shenle-web-record record <url>
```

它会启动一个 Chromium 浏览器，注入一个右下角的浮动 SNAP 面板，用户每点击一次 SNAP 就把当时的「截图 + DOM/a11y 快照」写入一个按时间戳命名的批次目录。

**你的职责不是直接调 Playwright，而是作为对话接口编排这个 CLI**：校验环境 → 拿 URL → 启动录制 → 把批次号和目录回报给用户。

## 何时使用本技能

用户想要把一个**正在运行的网页**录成本地文件（截图 + DOM 快照），用来后续分析、归档、或者交给别的 AI 看。典型场景：

- 「帮我录制一下后台登录页」
- 「把 https://example.com/admin 截一下」
- 「采集一下这个网站首页和搜索页」
- 「我想要这个站点的 DOM 快照」

**不要**用于：编辑 HTML、用结构化选择器抓数据、跑单测、或者不需要批次的单张截图。

## 工作流（四步，按顺序执行）

每一步都有明确的退出条件，没完成前不要跳到下一步。

### 第一步：环境检查

> **⚠️ 版本硬约束：本项目只支持 Playwright 1.57.x，不要装更高版本。**
>
> 原因：本机 `C:\Users\95431\AppData\Local\ms-playwright\` 已装的 chromium 是 **1200 / 1217 / 1223 / 1226**（对应 Playwright 1.57.x 的内置浏览器版本），缺 chromium-**1243**（Playwright 1.63 要求的）。如果 `.venv` 里被升到了 1.63，CLI 启动时会报：
>
> ```
> BrowserType.launch: Executable doesn't exist at C:\Users\95431\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe
> ```
>
> 所以 `.venv` 里的 playwright 必须钉死在 1.57（见下方检查项）。如果发现版本不对，**先降版本**，不要去装 chromium-1243。

在项目根目录 `D:\Code\AIQECourse\Phase2` 下依次执行：

```bash
python --version
python -m playwright --version
python -c "from importlib.metadata import version; print('playwright:', version('playwright'))"
```

**期望结果（全部必须命中）**：

- Python ≥ 3.11（与 `pyproject.toml` 中的 `requires-python` 一致）
- `python -m playwright --version` 输出 **`Version 1.57.x`**（必须是 1.57，不能是 1.63 或更高）
- `playwright` 包的 metadata 版本同样是 `1.57.x`

然后确认 Chromium 内核已经下载：

```bash
python -m playwright install --dry-run chromium
```

期望输出里包含 `chromium-1200` 这一行（即 Playwright 1.57 默认带的浏览器版本）。如果只有 1243 / 1244 等更高版本号，说明环境不对——按下方表格修复。

如果有任何一项不通过，**停下来告诉用户具体缺什么、需要装什么**。**不要**未经同意自动安装——Chromium 下载是几百 MB 的事。

按下面这张表逐条给出对应的安装命令：

| 缺失项 | 安装命令 |
| --- | --- |
| Python 版本过低 | 去 python.org 安装 3.11+ 后重试 |
| `playwright` 包缺失或版本不对（>1.57） | `pip install "playwright==1.57.0"`（**必须钉死**，不要 `pip install playwright`） |
| `shenle-web-record` 包缺失 | `pip install -e apps/shenle-web-record` |
| Chromium 内核缺失（应有 chromium-1200） | `python -m playwright install chromium`（会自动装 1200，**不要**指定其他版本） |

四项全部通过才进入第二步。

**附：环境里其实有两份 Playwright，要注意 PATH 顺序**

系统上一共有三个 `shenle-web-record.exe`（PATH 顺序决定用哪个）：

| 路径 | Playwright | 期望 Chromium |
| --- | --- | --- |
| `D:\Code\AIQECourse\Phase2\.venv\Scripts\shenle-web-record.exe` | 1.57.x（项目要求） | chromium-1200 ✅ |
| `C:\Users\95431\AppData\Local\Programs\Python\Python311\Scripts\shenle-web-record.exe` | 1.57.0 | chromium-1200 ✅ |
| `D:\Users\95431\AppData\Local\Programs\Python\Python39\Scripts\shenle-web-record.exe` | 1.57.0 | chromium-1200 ✅ |

本技能默认走 `.venv` 那份（最上面的）。如果 shell 的 PATH 让系统 Python 的 shenle-web-record 排在前面也没问题——三份都能正常用，只是不要去碰任何 `playwright > 1.57` 的版本。

### 第二步：确认目标 URL

如果用户在同一条消息里已经把 URL 一并给了，直接用，跳到第三步。

如果没给，**主动、明确地询问**：

> 请提供一下要录制的页面 URL，例如 `https://admin.example.com/login`。

**不要猜**。**不要**自作主张挑一个首页。URL 错了会让一次数分钟的录制全部作废。

如果用户给的 URL 看起来不合法（缺协议、缺主机名），指出来并请用户重新提供。

### 第三步：启动录制

从项目根目录进入 `apps/shenle-web-record/` 再执行 CLI，这样默认的输出目录 `AI-信息采集/` 会落在 `apps/shenle-web-record/AI-信息采集/` 下（也就是 CLI 的工作目录）：

```bash
cd apps/shenle-web-record
shenle-web-record record "<url>"
```

CLI 在跑的过程中，**按阶段向用户实时反馈**：

1. 「正在打开浏览器…」—— Chromium 窗口启动中。
2. 「正在导航到 `<url>`…」—— 页面加载中。
3. 「录制进行中」—— 浮动 SNAP 面板已就绪，用户可以填「模块 / 功能点 / 页面描述」然后点 SNAP。
4. 「等待用户结束会话（Ctrl+C）」—— 直到用户在终端按 `Ctrl+C`。

会话是**交互式**的，CLI 会一直挂着直到用户主动结束。**不要**自己加超时，**不要**替用户按终止。让用户掌控录制节奏。

### 第四步：返回结果

用户在终端按 `Ctrl+C`、或者明确说「录完了」「结束」「退出」之后，总结并回报：

- **批次号**：`YYYYMMDD-HHmmss`（CLI 在会话启动时生成的一次性时间戳）
- **输出目录**：`apps/shenle-web-record/AI-信息采集/<批次号>/`
- **结构提示**：每一组截图都在
  `<批次号>/<模块分段路径>/<功能点>/{img,json}/<NNN>.{png,json}` 下。

最后用一句自然的收尾，把后续步骤交给用户决定（**不要**自作主张去分析）：

> 录制完成！批次号 `<批次号>`，已保存到「`AI-信息采集/<批次号>/`」目录。
> 接下来需要我帮你分析这些截图和 DOM 吗？

## 输出约定

- 路径一律用项目相对路径，不要用 `~` 缩写。
- 用户态消息中的 URL 用反引号包起来。
- 状态消息用中文，跟用户语言保持一致；用户切到英文就把状态串改英文，但 CLI 调用方式不变。
- 路径里有中文目录（如 `AI-信息采集`）原样保留，不要转义。

## 边界情况

- **`shenle-web-record` 不在 PATH**：降级用 `python -m shenle_web_record <args>`，或者直接 `python src/shenle_web_record/cli.py <args>`（都要在 `apps/shenle-web-record/` 目录下）。
- **9222 端口被占用**：上一次 `shenle-web-record` 还在跑。问用户是要「接上现有的」还是「开一个新的」。
- **一次 SNAP 都没按就被中断**：批次目录其实已经创建好了（CLI 在启动时就建好了），照常回报批次号，但额外说一句「本次未写入任何截图」。
- **录制中途用户说「暂停」**：CLI 不支持暂停，老老实实告诉用户需要 `Ctrl+C` 结束后重启会话。

## 边界与反例

### 不要做（每条都给原因）

- **NEVER** 不要把录制当成自动化——录制产物只覆盖这一次路径，参数与断言仍需人工补
- **NEVER** 不要在录制中顺手改业务数据——录制会真实写库，污染后续用例
- **NEVER** 不要跳过回放验证——没回放过的录制脚本可用性接近 0

### 失败与兜底

| 现象 | 处理 |
| --- | --- |
| SNAP 点不动 | 确认浏览器是 headed 且页面已聚焦 |
| 回放失败 | 检查选择器是否为随机类名，必要时换成 data-testid |
| 步骤缺失 | 录制过程不要切换标签页，跨标签页需要手动补 |

### 何时不该用这个 skill

- 只需要读文档或写笔记：走知识库，不要调执行类命令。
- 需要改被测系统的业务数据：先确认数据隔离，再考虑用录制/回放。

## 执行顺序（顺序错了会白跑）

1. 先起 headed 浏览器，再录制。
2. 先走主路径，再补断言。
3. 先回放一次，再入库。
4. 先脱敏，再提交。

### 再加一条红线

- **NEVER** 不要把凭据留在录制文件里——录制默认会带真实 token，提交即泄露

### 兜底原则

任何一步失败，先留证（截图、响应体、日志），再重试；没有证据的重跑只会把问题变成偶发。
