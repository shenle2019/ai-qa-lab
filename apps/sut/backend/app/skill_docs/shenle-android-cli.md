---
name: shenle-android-cli
allowed-tools: Bash(shenle-android-cli:*) Bash(python:*)
description: "需要在安卓真机或模拟器上完成点击、输入、截图与界面断言时时使用。支持 android, adb, uiautomator, 真机, 设备 相关操作；Use when the task involves android / adb / uiautomator / 真机 / 设备.。触发词：cli / record / runner / adapter / skill。"
---

# shenle-android-cli

命令行驱动的 Android UI 自动化工具（adb shell input）。AI 按自然语言调用底层 CLI，无需 selector / ref / xpath。

## Quick start

```bash
# 1) 看设备
shenle-android-cli devices
# → emulator-5554   device
# → 12345678        device

# 2) 启动一个 App（activity 可省，默认走 monkey 找 launcher）
shenle-android-cli launch com.android.settings
# → [OK] launch: com.android.settings/.Settings → Events injected: 1

# 3) 截图存证
shenle-android-cli screenshot ./shot.png
# → [OK] screenshot: ...\shot.png (1080x2400) [png]

# 4) AI 视觉定位 + 点击
shenle-android-cli click "搜索按钮" --screenshot ./after-click.png
# → [OK] click "搜索按钮": (720, 230); shot=...ms ai=...ms total=...ms; post=...\after-click.png

# 5) AI 视觉定位输入框 + 输入文本（中文 OK）
shenle-android-cli input "搜索框" "你好世界"
# → [OK] input "搜索框" "你好世界": (720, 230); shot=...ms ai=...ms type=...ms total=...ms

# 6) 回到桌面（Home 键，进程保留；冷启动测试用 `stop`）
shenle-android-cli close
```

## Lifecycle

```bash
shenle-android-cli --version
shenle-android-cli --help

shenle-android-cli start [-s SERIAL]
# 选定目标设备并打印选中信息；不持久化 session，下次还会重新跑 `adb devices -l`

shenle-android-cli close                       # Home 键回到桌面（App 进程保留）
shenle-android-cli stop <pkg>                  # am force-stop，杀进程（冷启动测试用）

shenle-android-cli <任何命令> [-s SERIAL] [--debug]
# -s / --serial：指定设备序列号（多设备场景下避免被自动选错）
# --debug：AI 类命令保存「红框标注图」到 cwd；内部异常打印完整堆栈
```

> **Phase 1 不持久化"当前选中的设备"**：多设备场景下要么每条命令都显式 `-s`，要么按 adb 列出顺序把目标设备排第一。

## 设备选择规则（Phase 1）

每条需要设备的命令独立跑 `adb devices -l`，按以下规则选定：

1. 用户显式传 `-s SERIAL`：精确匹配；状态非 `device` 时给出友好提示
2. 用户没传：取列表里第一台 `state == "device"` 的设备

后续会引入 session 持久化（类似 shenle-web-cli 的 state.json）。

## Commands

**MANDATORY — 先读整个文件**：`references/detail.md`（178 行，覆盖「Commands」的完整细节）。
**不要加载** 其他 references 文件，本任务只需要这一份。

## 通用 flag

下面这些 flag 加在大多数命令后面都行：

```bash
shenle-android-cli <command> [args] -s <SERIAL>
shenle-android-cli <command> [args] --serial <SERIAL>
# 指定连哪台设备（多设备场景；默认取 adb 列表第一个 state==device）

shenle-android-cli <command> [args] --debug
# 调试模式：
#   - click / input / longpress / swipe --region / batch 会保存「AI 红框标注图」
#     到 cwd/shenle-debug-<cmd>-<ts>.png（默认行为；不污染 cwd）
#   - 打印 bbox 换算过程 + 各阶段耗时（毫秒）
#   - 内部异常时打印完整堆栈

shenle-android-cli click/input/swipe-to <args> --screenshot POST_PATH
# 操作完成后额外保存一张操作后截图（不带框），方便回归取证
```

## 元素定位（AI 视觉）

`click` / `input` / `longpress` / `batch click|longpress` / `swipe --region` / `get` 的 AI 元素定位遵循这套约定：

- **坐标系**：0-1000 **归一化坐标**，与图片实际像素无关。本地按真实截图尺寸换算成像素中心。
  - AI 返回 `[xmin, ymin, xmax, ymax]`（0-1000 整数）
  - 像素中心 = `((xmin+xmax)/2 * img_w/1000, (ymin+ymax)/2 * img_h/1000)`
- **描述**：自然语言，写「登录按钮」「用户名输入框」「左侧菜单」即可。
- **输入框**：点输入框本身（不是 label 文字）。
- **bbox 容差**：太小（<5x5 像素）会报 `[FAIL]` 重试。

## Batch — 一次截图 + 一次 AI 识别多个元素

> **多步操作优先用 batch**：只截一次图、只调一次 AI，按顺序执行。比串行 click/input 快很多、AI 准确率也更高（一次看到所有目标）。

支持的 5 种操作（空格分隔；描述可含空格；input 用 `::` 把描述和文本分开）：

| 操作 | 语法 | 说明 |
| --- | --- | --- |
| `click` | `click <描述>` | AI 视觉定位并点击 |
| `input` | `input <描述>::<文本>` | AI 视觉定位输入框并填入（**batch input 固定走屏幕中心**，不走 AI） |
| `click-at` | `click-at <x> <y>` | 无 AI，点击原始坐标 |
| `input-at` | `input-at <x> <y> <文本>` | 无 AI，点击坐标后输入 |
| `longpress` | `longpress <描述> [--duration N]` | AI 视觉定位 + 长按（默认 1500ms） |

**示例**：

```bash
# 登录表单：填用户名 + 密码 + 点登录（3 步，1 次 AI）
shenle-android-cli batch input "用户名::admin" input "密码::123456" click "登录"

# 混合 AI 和坐标（先点搜索框坐标 → AI 识别搜索按钮 → 点提交）
shenle-android-cli batch click-at 100 200 click "搜索按钮"

# 长按元素
shenle-android-cli batch longpress "我的头像" --duration 2000

# 调试：加 --debug 看每步 AI 返回的 bbox + 标注图
shenle-android-cli --debug batch input "用户名::admin" input "密码::123" click "登录"
# → [OK] batch: 3/3 ops total=...ms shot=...ms ai=...ms ops=...ms
# → ai框=shenle-debug-batch-<ts>.png
```

**性能对比**（300ms AI 延迟 + 真实 screencap，3 次 click 操作）：

```
串行（3 条独立 click）：4.33s
batch（1 条 batch click×3）：2.42s
batch 比 serial 快 1.91s（44%）
```

## 中文输入（关键，避免乱码）

`adb shell input text` 对非 ASCII（中文 / emoji）会丢字符或乱码。
本工具对 **非 ASCII 文本** 强制走 Android 10+ 的标准剪贴板方案：

```
adb shell cmd clipboard set-primary-clip --user 0 <文本>   # 写入
adb shell cmd clipboard get-primary-clip --user 0          # 读回校验
adb shell input keyevent 279                              # 触发粘贴
```

如果设备 / ROM 不支持 `cmd clipboard`（vivo / ColorOS / HyperOS 等定制 ROM 常见、部分模拟器镜像也没有），**不会**回退到 `input text`——会直接报错并提示装 [ADBKeyboard](https://github.com/senzhk/ADBKeyBoard) 兜底：

```
[FAIL] input: 剪贴板方案不可用（set-primary-clip 失败：No shell command implementation.）。
        常见于 vivo/ColorOS/HyperOS 等定制 ROM。请改用 ADBKeyboard：装好 APK →
        切到 ADBKeyboard 输入法 → 用 `adb shell am broadcast -a ADB_INPUT_TEXT
        --es msg '...'` 输入。
```

> "看似成功但内容乱码" 比 "明确失败" 更危险（用例静默通过），所以宁可报错也不兜底。

通过 `--input-method adbkeyboard` 或环境变量 `INPUT_METHOD=adbkeyboard` 切换到 ADBKeyboard 路径。

## 冷启动 vs 热启动

```bash
shenle-android-cli stop com.android.settings       # am force-stop，杀进程
# → [OK] stop: com.android.settings 已强制停止（am force-stop）

shenle-android-cli launch com.android.settings    # 冷启动
# → [OK] launch: com.android.settings ... → Events injected: 1

shenle-android-cli close                           # Home 键，保留进程
# → [shenle] 已回到桌面（device=emulator-5554）

shenle-android-cli shell dumpsys activity processes | grep com.android.settings
# → *APP* UID 1000 ProcessRecord{... com.android.settings/1000}    # 进程还在
```

- `stop` = 杀进程（**冷启动测试**）
- `close` = Home 键（**热切换**，进程保留）

## AI 红框标注图（`--debug`）

`--debug` 时启用，AI 类命令把用过的那张截图画红框 + 标签，保存到 `cwd/shenle-debug-<cmd>-<timestamp>.png`，路径打在 `[OK]` 行末尾：

```
# 不带 --debug：干干净净一行
$ shenle-android-cli click "搜索按钮"
[OK] click "搜索按钮": (720, 230); shot=469ms ai=812ms total=1281ms

# 带 --debug：多一张标注图 + 路径
$ shenle-android-cli --debug click "搜索按钮"
[OK] click "搜索按钮": (720, 230); shot=469ms ai=812ms total=1281ms; ai框=shenle-debug-click-1700000000000.png
```

点开 `ai框` 那张图能看到 AI 把元素框在了哪个位置——调试 AI 误识别时直接看图就行。
**默认不开 `--debug` 不生成**，避免每次跑都污染 cwd。

## Output format

每个命令统一走 **单行** + exit code，方便 AI / 脚本 parse：

| 场景 | 形态 | exit code |
| --- | --- | --- |
| 成功 | `[OK] <cmd> <args>: <result>` | 0 |
| 业务失败（参数 / 设备 / 包名 / 剪贴板 / AI 配置） | `[FAIL] <cmd> <args>: <msg>` | 1 |
| 内部未捕获异常（`--debug` 看堆栈） | `[FAIL] <cmd> <args>: <msg>` | 2 |
| 基础设施类失败（`devices` / `start` / `close`） | `[shenle] <msg>`（stderr） | 1 |
| AI debug（仅 `--debug`） | `[DEBUG] ...`（stderr） | — |
| 透传命令（`shell` / `appinfo`）的 [OK] | `[OK] ...`（stderr），原始输出 stdout | — |

**stdout / stderr 约定**：

- `[OK]` / `[FAIL]` 打 **stdout**（`start` / `close` / 透传命令的 [OK] 打 stderr）。
- `[DEBUG]` 打 **stderr**。
- `get` 命令的状态行 `[OK] get "..."` 打 **stderr**，4 节描述内容打 **stdout**——脚本可以直接 `capture` 正文。
- `shell` / `appinfo` 走透传：原始 stdout 原样 + 退出码原样返回。

## Environment variables

| 变量 | 用途 | 必需 |
| --- | --- | --- |
| `ANDROID_AI_API_KEY` | AI 网关 key | `click` / `input` / `longpress` / `batch click\|longpress` / `swipe --region` / `get` 必需 |
| `ANDROID_AI_BASE_URL` | AI 网关 base URL（不带 `/chat/completions` 后缀） | 同上 |
| `ANDROID_AI_MODEL` | 视觉模型名 | 同上 |
| `INPUT_METHOD` | 输入法方案（`clipboard` 默认 / `adbkeyboard`） | 可选 |

也支持从当前目录的 `.env` 自动加载（`python-dotenv`）。

> **环境变量前缀是 `ANDROID_AI_*`**（跟 web-cli's `WEB_AUTOMATION_AI_*` 区分），跟 `apps/shenle-android-cli/demo/demo_2.py` 一致。

`devices` / `start` / `launch` / `close` / `stop` / `current-app` / `screenshot` / `swipe`（无 `--region`）/ `swipe-to` / `zoom` / `pinch` / `keyevent` / `recents` / `notifications` / `dump-ui` / `shell` / `appinfo` 不需要 AI 配置。

## 常见问题

| 报错 | 原因 | 修复 |
| --- | --- | --- |
| `[FAIL] click: AI 配置缺失：ANDROID_AI_API_KEY、ANDROID_AI_BASE_URL、ANDROID_AI_MODEL。...` | CWD/.env 没配或缺变量 | 在当前目录写 `.env` 含这 3 个变量；改完直接再跑 click（无需重启） |
| `[FAIL] click: AI 服务不可达（http://...）：...` | CWD/.env 的 BASE_URL 不可达 | `curl <BASE_URL>/v1/models` 看通不通 |
| `adb: no devices/emulators found` | 没接设备 / USB 调试没开 / 没授权 | `adb devices` 看列表；插线 / 开 USB 调试 / 同意弹窗 |
| `am force-stop: ... package does not exist` | 包名错 | 用 `shenle-android-cli appinfo <pkg>` 先查 |
| `剪贴板方案不可用（set-primary-clip 失败：...）` | vivo / ColorOS / HyperOS 等定制 ROM 不支持 `cmd clipboard` | 装 [ADBKeyboard](https://github.com/senzhk/ADBKeyBoard) → 切到 ADBKeyboard 输入法 → `--input-method adbkeyboard` |
| `[FAIL] swipe: ... 设备存在 ...（`device=emulator-5554`）` | 多设备 + 没传 `-s` | 每条命令都加 `-s SERIAL`，或让目标设备在 `adb devices` 里排第一 |
| 截图上 AI 框的位置和实际元素差很远 | 描述不消歧 | 用 `--debug` 看 `shenle-debug-click-<ts>.png` 确认 AI 框在哪；改描述（加位置 / 颜色 / 文字） |
| `input` 中文看上去成功了但内容是乱码 | 不应该出现——本工具直接报错而不是兜底 | 走"中文输入"那段排查 |
| WheelPicker（省/市/区）滑动没反应 | `swipe up -c N` / `swipe-to --duration 50` / tap listitem —— 全部无效 | 必读 **WheelPicker / 省市区地址选择器** 那节：慢速拖动（duration 800~1500ms，距离 ≥ 700px），先 dump-ui 拿 picker bounds |

## Examples

**MANDATORY — 先读整个文件**：`references/detail-1.md`（104 行，覆盖「Examples」）。
**不要加载** 其他 references 文件。

## Specific tasks

* **批量操作 + 取证**：`batch` 一次截图 + 一次 AI 识别多个元素，按顺序执行 —— 性能 / 准确率都优于串行 click/input。
* **⚠️ WheelPicker（省/市/区地址选择器，物流类 App 必踩）**：fling / tap / 整屏 swipe 全都无效；只能 `swipe-to` 慢拖（duration 800~1500ms，distance ≥ 700px）。详见 **WheelPicker / 省市区地址选择器（强制 — 必读）**。
* **AI bbox 选偏了**：用 `--debug` 看 `shenle-debug-<cmd>-<ts>.png`；改描述（加位置 / 颜色 / 文字）。
* **中文输入乱码**：本工具直接 `[FAIL]` 不兜底，走"中文输入"那段排查：优先装 ADBKeyboard。
* **冷启动 vs 热启动**：测冷启动用 `stop <pkg>` 再 `launch`；测热切换用 `launch` + `close`（Home 键）。
* **多设备**：每条命令加 `-s SERIAL`；或让目标设备在 `adb devices -l` 里排第一。
* **跨会话保状态**：Android 自动化不像 web 自动化有持久 user-data-dir；登录态 / 数据都依赖 App 自己的持久化，不在本工具能力范围。

## 边界与反例

### 不要做（每条都给原因）

- **NEVER** 不要用坐标点击代替元素定位——不同分辨率与字体缩放下坐标必错，且无法解释失败原因
- **NEVER** 不要在输入前不清空输入框——残留文本会让断言通过但业务实际错误
- **NEVER** 不要假设设备一直在线——拔线、锁屏、休眠都会让 `uiautomator dump` 返回空，必须先判在线

### 失败与兜底

| 现象 | 处理 |
| --- | --- |
| `adb devices` 为空 | 检查 USB 调试与授权弹窗，无线调试需先 `adb pair` |
| dump 解析失败 | 确认返回里含 `<hierarchy`，否则多试一次并检查是否被系统弹窗覆盖 |
| 点击无反应 | 确认元素 clickable 或改用可点击祖先节点 |

### 何时不该用这个 skill

- 只需要读文档或写笔记：走知识库，不要调执行类命令。
- 需要改被测系统的业务数据：先确认数据隔离，再考虑用录制/回放。

## 执行顺序（顺序错了会白跑）

1. 先 `devices` 确认在线，再操作。
2. 先 dump 找到元素，再点击。
3. 先清空输入，再输入。
4. 先截图留证，再判定。

### 再加一条红线

- **NEVER** 不要在未确认前台 Activity 时断言——锁屏或通知栏会把断言指向错误页面

### 兜底原则

任何一步失败，先留证（截图、响应体、日志），再重试；没有证据的重跑只会把问题变成偶发。
