# 模块 04 笔记：不装 Playwright，怎么驱动浏览器

## 问题

项目里没有安装 Playwright，怎么证明“懂 Web 自动化”？

答案是直接和浏览器说话。Chrome/Edge 自带 Chrome DevTools Protocol（CDP）：启动时加一个远程调试端口，就能通过 WebSocket 发命令，导航、执行 JS、点击、填值、截图。

## 方案

包放在 `libs/miniplaywright`，不依赖 Playwright 库。

| 能力 | 实现 |
|---|---|
| 启动浏览器 | 本机 Edge/Chrome + `--remote-debugging-port` |
| 找页面 | `GET /json/list` 拿 `webSocketDebuggerUrl` |
| 导航 | `Page.navigate` |
| 定位 | `document.querySelector` |
| 点击/填值 | `Runtime.evaluate` + `input/change` 事件 |
| 自动等待 | 轮询选择器/期望，超时抛错 |
| 断言 | 文本、包含、可见、数量、URL、标题 |
| 截图 | `Page.captureScreenshot` |
| 报告 | 复用迷你 pytest 的 JSON/HTML |

## 结果

- 6 个框架元测试通过（本地静态 HTML）
- 5 个 SUT UI 用例通过（启动 SUT + Edge）
- 真实创建了一条工单，截图在 `docs/portfolio/screenshots/module-04-tickets.png`
- 报告：`docs/portfolio/module-04-playwright-report.html`

## 踩坑

1. Chrome 111+ 的 CDP WebSocket 需要 `--remote-allow-origins=*`。
2. `websockets.connect` 直接连接要加 `legacy=True`，否则有弃用警告。
3. Vue 的 `v-model` 只认 `input/change` 事件，光改 `el.value` 不生效。
4. 期望失败会落在框架文件里，要加 `__tracebackhide__` 并在 runner 里跳过。
5. SPA 的 hash 路由不会触发整页刷新，导航后要等目标选择器出现。

## 一句话

Web 自动化不是只有 Playwright。理解 CDP 这条底层通道，换任何 Chromium 浏览器都能驱动。
