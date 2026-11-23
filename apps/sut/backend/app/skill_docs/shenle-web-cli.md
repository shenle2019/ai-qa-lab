---
name: shenle-web-cli
allowed-tools: Bash(shenle-web-cli:*) Bash(python:*)
description: "需要用自然语言描述在网页上点击、输入、截图并读回页面状态时时使用。支持 web-cli, 浏览器, navigate, screenshot, 视觉定位 相关操作；Use when the task involves web-cli / 浏览器 / navigate / screenshot / 视觉定位."
---

# shenle-web-cli

命令行驱动的浏览器自动化工具（Playwright + CDP）。AI 按自然语言调用底层 CLI，无需 selector、ref、xpath。

## Quick start

```bash
# 1) 拉起后台浏览器（detached daemon，CLI 退出后浏览器继续跑）
shenle-web-cli start

# 2) 打开一个页面（自动补 https://，viewport 拉到 1440x900）
shenle-web-cli navigate https://example.com
# → [OK] navigate: https://example.com → title="Example Domain"

# 3) 截图存证（仅当前 viewport，非整页）
shenle-web-cli screenshot ./shot.png
# → [OK] screenshot: ...\shot.png (1440x900) [png]

# 4) AI 视觉定位 + 点击（让 AI 看到「More information」就点它）
shenle-web-cli click "More information" --screenshot ./after-click.png
# → [OK] click "More information": (820, 360); 截图 → ...\after-click.png

# 5) AI 视觉定位输入框 + 填文本（中文 / 长字符串都 OK）
shenle-web-cli navigate https://www.baidu.com
shenle-web-cli input "搜索框" "你好，世界"
# → [OK] input "搜索框" "你好，世界": (720, 240)

# 6) 关掉
shenle-web-cli close
```

## Lifecycle

```bash
shenle-web-cli start [--port 9222] [--headless]
shenle-web-cli close                    # close
                            # 不带 --port：关掉所有在跑的后台浏览器
shenle-web-cli close --port 9223      # 只关 9223 那个

shenle-web-cli --version
shenle-web-cli --help
shenle-web-cli --debug <command> [...]    # 任意命令加 --debug 看完整堆栈
```

- `start` 拉起的是 **脱离父进程的 daemon**——父 CLI 命令退出后浏览器仍常驻。
- Cookie / 登录态保存在固定的 per-port user-data-dir，下次 `start` 自动复用。
- 全局状态位置（Windows）：`%LOCALAPPDATA%\shenle-web-cli\`
  - `state\<port>.json` — 当前后台浏览器状态（per-port 一份）
  - `daemon.log` — 后台进程日志
  - 数据目录：`<start 时的 cwd>\user_data\<port>\`

## Commands

**MANDATORY — 先读整个文件**：`references/detail-1.md`（135 行，覆盖「Commands」）。
**不要加载** 其他 references 文件。

## 通用 flag

下面这些 flag 加在 `navigate / screenshot / click / input / scroll / get / url / title / batch / click-at / input-at / swipe-to` 任何一个后面都行：

```bash
shenle-web-cli <command> [args] --port 9223
# 指定连哪个端口的后台浏览器（默认从 state.json 读，9222 起）
# 同时跑多套浏览器时用

shenle-web-cli <command> [args] --headless          # 仅 start 有意义
shenle-web-cli <command> [args] --debug             # 内部异常打完整堆栈

shenle-web-cli <command> [args] --on-dialog accept
shenle-web-cli <command> [args] --on-dialog dismiss
shenle-web-cli <command> [args] --on-dialog accept --prompt-text "默认文本"
# alert/confirm/prompt 弹窗处理策略：
#   accept        → 弹窗期间任何 dialog 出现都点确定
#   dismiss       → 弹窗期间任何 dialog 出现都点取消
#   accept + --prompt-text → prompt 弹窗填入文本再确定
# 不传：dialog 一旦出现会卡住后续命令

shenle-web-cli click/input "x" ... --enhanced "右上角、蓝色"
# click / input / scroll --region 追加消歧描述，避免 AI 选错
```

## 元素定位

`click` / `input` / `scroll --region` / `get` / `batch` 的 AI 元素定位遵循这套约定：

- **坐标系**：0-1000 **归一化坐标**，与图片实际像素无关。本地按真实截图尺寸换算成像素中心。
  - AI 返回 `[xmin, ymin, xmax, ymax]`（0-1000 整数）
  - 像素中心 = `((xmin+xmax)/2 * img_w/1000, (ymin+ymax)/2 * img_h/1000)`
- **描述**：自然语言，写「登录按钮」「用户名输入框」「左侧菜单」即可。多个相似元素时用 `--enhanced` 加位置 / 颜色 / 标签消歧。
- **输入框**：点输入框本身（不是 label 文字）。
- **bbox 容差**：太小（<5x5 像素）会报 `[FAIL]` 重试。

## 弹窗处理

```bash
# 假设某个 click 会触发 confirm，直接 dismiss
shenle-web-cli click "删除" --on-dialog dismiss

# 假设某个 navigate 会触发 prompt，填默认值后确定
shenle-web-cli navigate https://example.com/login --on-dialog accept --prompt-text ""

# 不知道会不会弹 → 不传；万一弹了命令会卡直到浏览器 dismiss 它
```

## Output format

每个命令统一走 **单行** + exit code，方便 AI / 脚本 parse：

| 场景 | 形态 | exit code |
| --- | --- | --- |
| 成功 | `[OK] <cmd> <args>: <result>` | 0 |
| 业务失败（AI 配置缺、元素找不到、CDP 连不上） | `[FAIL] <cmd> <args>: <msg>` | 1 |
| 内部未捕获异常 | `[FAIL] <cmd> <args>: <msg>` | 2 |
| 弹窗处理日志（不影响成功） | `[DIALOG] type=confirm message='...' → accept` | — |
| AI debug（仅 `--debug`） | `[DEBUG] ...`（打到 stderr） | — |

`start` / `close` 例外：失败时打 `[shenle] ...`（stderr），不走 `[FAIL]`。

**stdout / stderr 约定**：

- `[OK]` / `[FAIL]` 打 **stdout**。
- `[DIALOG]` / `[DEBUG]` / `get` 命令的状态行 打 **stderr**。`get` 的 4 段结构化文本打 **stdout**，脚本可以直接 `capture`。
- 多行输出用 `head -n 1` 拿结果行就行。

## Environment variables

| 变量 | 用途 | 必需 |
| --- | --- | --- |
| `WEB_AUTOMATION_AI_API_KEY` | AI 网关 key | `click` / `input` / `scroll --region` / `get` / `batch` 必需 |
| `WEB_AUTOMATION_AI_BASE_URL` | AI 网关 base URL（不带 `/chat/completions` 后缀） | 同上 |
| `WEB_AUTOMATION_AI_MODEL` | 视觉模型名 | 同上 |

也支持从当前目录的 `.env` 自动加载（`python-dotenv`）。

`navigate` / `screenshot` / `url` / `title` / `click-at` / `input-at` / `swipe-to` 不需要 AI 配置。

## 多套浏览器（--port）

每个端口一份独立后台浏览器 + 独立 user-data-dir，可以同时跑多套（例如一个无头跑用例、一个有头做手动调试）：

```bash
shenle-web-cli start --port 9222          # 第一套（有头）
shenle-web-cli start --port 9223 --headless   # 第二套（无头）

shenle-web-cli --port 9222 click "登录"
shenle-web-cli --port 9223 click "登录"

shenle-web-cli list-ports                  # 等价于：列出 state 下所有 running 端口
# 实际写法：shenle-web-cli close 不带 --port 会关掉所有 running
```

## Examples

### 表单提交

```bash
shenle-web-cli start
shenle-web-cli navigate https://example.com/form
shenle-web-cli screenshot ./before.png

shenle-web-cli batch input "邮箱::user@example.com" input "密码::secret123" click "提交"
shenle-web-cli screenshot ./after.png

shenle-web-cli url
shenle-web-cli close
```

### 跑一轮回归（多条用例串行）

```bash
shenle-web-cli start

# 用例 1
shenle-web-cli navigate https://shop.example.com
shenle-web-cli batch click "登录入口" input "手机号::13800000000" input "密码::xxx" click "登录"
shenle-web-cli screenshot ./case1.png
shenle-web-cli url                                    # 断言 → /home

# 用例 2
shenle-web-cli navigate https://shop.example.com/search
shenle-web-cli batch input "搜索框::手机" click "搜索"
shenle-web-cli scroll down -c 5
shenle-web-cli screenshot ./case2.png
shenle-web-cli get "搜索结果列表"                     # 取证：AI 描述列表内容

shenle-web-cli close
```

### 弹窗 / 拖拽 / 滚动取证

```bash
shenle-web-cli navigate https://example.com/list
shenle-web-cli scroll down -c 10 --region "结果列表" --screenshot ./scrolled.png
shenle-web-cli swipe-to 500 800 500 200              # 上滑刷新 / 加载更多
shenle-web-cli click "确认" --on-dialog accept
```

### Debug 单条 AI 命令

```bash
shenle-web-cli navigate https://example.com
shenle-web-cli --debug click "登录" --screenshot ./after.png
# → [DEBUG] AI 描述: 登录
# → [DEBUG] 截图尺寸: 1440x900
# → [DEBUG] AI 返回 (0-1000): [...]
# → [DEBUG] 缩放因子: x=1.440, y=0.900
# → [DEBUG] bbox (像素): [...]
# → [DEBUG] 中心 (像素): (820, 360)
# → [DEBUG] 标注图: <cwd>\shenle-debug-click-<ts>.png
# → [OK] click "登录": (820, 360); 截图 → ...\after.png
```

标注图（带红框 + 编号）在 `<cwd>\shenle-debug-<cmd>-<ts>.png`，AI 选错位时打开看就清楚。

## Specific tasks

* **批量操作 + 取证**：`batch` 一次截图 + 一次 AI 识别多个元素，按顺序执行 —— 性能 / 准确率都优于串行 click/input。
* **AI bbox 选偏了**：加 `--enhanced` 给位置 / 颜色 / 文字消歧；或加 `--debug` 看标注图。
* **跑不通先看 daemon 日志**：Windows 上是 `%LOCALAPPDATA%\shenle-web-cli\daemon.log`，daemon 死了 / Chromium 启动失败 / CDP 拒绝连接都在里头。
* **跨会话保登录态**：cookie 存在 `<start 时的 cwd>\user_data\<port>\`，下次 `start --port <同端口>` 自动复用。不要在临时目录里 start。

## 边界与反例

### 不要做（每条都给原因）

- **NEVER** 不要在未 `start` 时直接 `navigate`——浏览器实例不存在时会挂到超时，且报错指向导航而不是启动
- **NEVER** 不要把视觉模型给的 bbox 当像素坐标用——多数视觉模型返回的是相对近似框，直接点会偏出元素
- **NEVER** 不要用整串文本匹配代替描述定位——文案会随版本变化，描述定位抗改动

### 失败与兜底

| 现象 | 处理 |
| --- | --- |
| `start` 30s 超时 | 给子进程设 `PLAYWRIGHT_BROWSERS_PATH`，并换一个未被占用的 `--port` |
| 点击位置偏移 | 先用 `screenshot` 留证，再改用 `get` 读结构后用元素定位 |
| 视觉模型 404/403 | 确认 base_url、model 名与 key 属于同一供应商，必要时换 `qwen3-vl-plus` |

### 何时不该用这个 skill

- 只需要读文档或写笔记：走知识库，不要调执行类命令。
- 需要改被测系统的业务数据：先确认数据隔离，再考虑用录制/回放。

## 执行顺序（顺序错了会白跑）

1. 先 `start`，再 `navigate`。
2. 先截图，再视觉定位。
3. 先读结构（`get`），再点坐标。
4. 先 `close`，再起下一个会话。

### 再加一条红线

- **NEVER** 不要复用上一次的浏览器端口——端口占用会让 `start` 挂起，错误却显示为启动超时

### 兜底原则

任何一步失败，先留证（截图、响应体、日志），再重试；没有证据的重跑只会把问题变成偶发。
