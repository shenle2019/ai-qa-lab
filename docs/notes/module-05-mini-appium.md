# 模块 05 笔记：不装 Appium，怎么测 Android

## 问题

项目里没有 Appium Server，怎么证明“懂移动端 UI 自动化”？

答案是直接走 Android 底层：ADB 发命令，UIAutomator 导出控件树，找到节点坐标，`input tap` 点击，`screencap` 截图。

## 方案

包放在 `libs/miniappium`，不依赖 Appium。

| 能力 | 实现 |
|---|---|
| 设备发现 | `adb devices` |
| 启动 App | `am start -a android.settings.SETTINGS` |
| 控件树 | `uiautomator dump` + `adb exec-out cat` |
| 定位 | text / resource-id / content-desc / class |
| 点击 | 算 bounds 中心 + `input tap` |
| 输入 | `input text`（英文优先） |
| 返回/Home | `input keyevent 4/3` |
| 自动等待 | 轮询 dump，超时抛错 |
| 截图 | `adb exec-out screencap -p` |
| 报告 | 复用迷你 pytest 的 JSON/HTML |

## 结果

- 5 个框架元测试通过
- 3 个 Settings 演示通过
- 真实打开 Settings、点击 Network & internet、返回首页
- 截图在 `docs/portfolio/screenshots/module-05-settings.png`
- 报告：`docs/portfolio/module-05-appium-report.html`

## 踩坑

1. Git Bash 会把 `/sdcard/...` 转成 Windows 路径，命令要加 `MSYS_NO_PATHCONV=1`，或者用 Python subprocess 传参数列表。
2. Settings 会恢复上次页面，先 `am force-stop` 再启动。
3. `uiautomator dump` 每次约 0.5 秒，轮询间隔别太短。
4. `adb input text` 对中文不稳定，demo 用英文界面。
5. 模拟器启动慢，先等 `sys.boot_completed=1`。

## 一句话

Appium 的底层也是 ADB/UIAutomator。把这条链路走通，就能解释移动端自动化到底在做什么。
