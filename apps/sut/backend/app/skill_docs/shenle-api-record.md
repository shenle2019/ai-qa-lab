---
name: shenle-api-record
description: "需要抓取接口请求并沉淀成可执行的接口资产或用例时时使用。支持 api-record, 抓包, 代理, 证书, 请求模板 相关操作；Use when the task involves api-record / 抓包 / 代理 / 证书 / 请求模板."
---

# shenle-api-record

这是一个**驱动类技能**：把本地 `shenle-api-record` 这个 Python CLI 包成对话式的工作流。

底层 CLI 位于 `apps/shenle-api-record/`，已实现的子命令：

```
shenle-api-record record        # 启动 mitmweb 录制（带 SPA 控制面板 + 右下角 Stop 按钮，Ctrl+C 结束）
shenle-api-record record --no-browser  # 同上，但不自动开浏览器（H5/APP/桌面应用场景）
shenle-api-record install-ca    # 生成（如果缺）并尝试装到系统信任库
shenle-api-record check         # 一键环境报告（Python / mitmproxy / CA / certutil）
shenle-api-record stop          # 停止后台录制
```

> 取摘要**不靠 CLI 子命令**，靠独立脚本 `apps/shenle-api-record/skill/shenle-api-record/scripts/inspect_recording.py`（详见第五步）。CLI 没有 `inspect` 子命令。

**你的职责不是直接调 mitmproxy 或自己拼 subprocess，而是作为对话接口编排这个 CLI**：校验环境 → 拿目标 → 启动录制 → 指导配代理 → 取摘要交给用户。

## 何时使用本技能

用户想把某个**正在运行的客户端**（浏览器 / 手机 H5 / APP / 桌面应用）发出去的 HTTP/HTTPS 接口都抓成本地文件，用来后续分析、归档、生成接口文档或测试用例。典型场景：

- 「帮我录一下购物车 App 的接口」
- 「把后台登录到下单的接口都抓下来」
- 「HTTPS 解不开，先帮我把 CA 装上」
- 「手机 H5 的接口抓一下」
- 「桌面端那个客户端的网络请求都录一下」
- 「接着上一次那批继续录」

**不要**用于：

- 想要 UI 截图 / DOM 快照（用 `shenle-web-record` 或 `shenle-device-record`）
- 想要结构化爬某个站点的数据（用别的选择器工具）
- 单次 `curl` 调试（直接用 curl + `--cacert` 即可）
- 不需要批次的即时抓包（直接 Wireshark / Fiddler 之类）

## 工作流（五步，按顺序执行）

**MANDATORY — 先读整个文件**：`references/detail-1.md`（227 行，覆盖「工作流（五步，按顺序执行）」）。
**不要加载** 其他 references 文件。

## 输出约定

- 路径一律用项目相对路径，不要用 `~` 缩写。
- 端口 / URL 在用户态消息里用反引号包起来（如 `` `127.0.0.1:8080` ``）。
- 状态消息用中文，跟用户语言保持一致；用户切到英文就把状态串改英文，但 CLI 调用方式不变。
- 路径里的中文目录（如 `AI-信息采集`）原样保留，不要转义。
- 给用户的指引里提到 LAN IP 时**必须用真实的电脑 IP**（跑一次 Python one-liner 拿），不要写 `localhost` / `127.0.0.1`——手机上的代理写 `127.0.0.1` 指的是手机自己，不是电脑。

## 边界情况

- **`shenle-api-record` 不在 PATH**：降级用 `python -m shenle_api_record <args>`（都要在 `apps/shenle-api-record/` 目录下）。脚本会装到 `.venv\Scripts\shenle-api-record.exe`，如果 PATH 里没有就先 `pip install -e apps/shenle-api-record`。
- **8080 端口被占用**：上一次录制还没退干净，或别处占着。问用户是要「接上现有的」还是「先杀掉再开新的」（杀进程需要用户授权）。改端口**不推荐**——会跟代理配置指引对不上。
- **`mitmdump.exe` / `mitmweb.exe` 不存在**（罕见）：用户装过 mitmproxy 又卸了，或者装到了另一个 venv。`pip show -f mitmproxy` 看实际路径，让用户 `pip install --force-reinstall mitmproxy`。
- **手机连不上代理**：三件事按顺序查——(1) 电脑 IP 是不是真的从 Wi-Fi 适配器拿的（不要拿 VirtualBox / WSL / Docker 网卡的）；(2) 手机和电脑是不是同一个网段（`192.168.1.x` vs `192.168.50.x` 这种路由器隔离的）；(3) 电脑防火墙有没有放行 8080（Windows Defender 默认会拦，给个入站规则：`netsh advfirewall firewall add rule name="mitmproxy" dir=in action=allow protocol=TCP localport=8080`，**需要用户授权再跑**）。
- **APP 抓不到 HTTPS**：99% 是没把 CA 装进 APP 信任库，按第四步 B 的 Android 7+ 指引处理。Android 7+ 不允许 APP 信任用户 CA 是 Google 的硬约束，绕不开就只能换思路（H5 入口 / 反编译 / Frida hook）。
- **录制中途用户说「暂停」**：CLI 不支持暂停，老老实实告诉用户需要 `Ctrl+C` / Stop 后重启会话，下次可以加 `--continue-batch` 风格复用批次号。
- **`record` 模式下用户关掉了浏览器**：CLI 不退出，SPA 关了只是看不到预览，录制照常进行；想看预览就再开 `http://127.0.0.1:8081/`。
- **inspect 脚本输出 "no recordings found"**：批次目录其实已经创建（CLI 启动时就建好），但用户在配代理阶段就退了。照常回报批次号 + 目录路径，附「本次未抓到任何接口」。
- **inspect 脚本报 "expected JSON array"**：原始文件被中途损坏（一般是磁盘满或被杀进程）。提示用户删除该 `rawNN.json` 后重录，或加 `--details` 看其它文件。
- **inspect 脚本路径不对**：必须用 `apps/shenle-api-record/skill/shenle-api-record/scripts/inspect_recording.py`（脚本只在 apps 端存在；`.claude/skills/` 是 SKILL.md 的加载副本，不带 scripts 目录）。
- **同一批次需要多次录制合并**：CLI 没有内置合并，跑第二次时显式传 `--output-root apps/shenle-api-record/AI-信息采集/<旧批次>` 复用同一目录即可（`rawNN.json` 编号会自然递增，不会覆盖）。

## 边界与反例

### 不要做（每条都给原因）

- **NEVER** 不要用抓包结果直接回归——抓到的是一次性的真实数据，直接重放多半违反业务约束
- **NEVER** 不要忽略证书安装——HTTPS 抓不到包，多半是设备未信任代理证书
- **NEVER** 不要把 token 写进资产——资产会被提交与共享，凭据必须走环境变量

### 失败与兜底

| 现象 | 处理 |
| --- | --- |
| 抓不到请求 | 确认设备代理与端口一致，且证书已信任 |
| 只有请求没有响应 | 关闭 HTTP/2 或改用明文测试端点 |
| 重放 401 | 先登录刷新 token，再重放业务请求 |

### 何时不该用这个 skill

- 只需要读文档或写笔记：走知识库，不要调执行类命令。
- 需要改被测系统的业务数据：先确认数据隔离，再考虑用录制/回放。

## 执行顺序（顺序错了会白跑）

1. 先配代理与证书，再抓包。
2. 先筛业务请求，再存资产。
3. 先参数化，再回放。
4. 先脱敏，再提交。

### 再加一条红线

- **NEVER** 不要用抓包数量衡量覆盖——抓到的多是重复轮询，真正写接口往往只出现一次

### 兜底原则

任何一步失败，先留证（截图、响应体、日志），再重试；没有证据的重跑只会把问题变成偶发。

## 一页速查

| 想做什么 | 怎么做 |
| --- | --- |
| 抓一个新接口 | 起代理后操作 App 或页面，只留业务 host |
| 只看有用的请求 | 按 host+path 过滤，丢掉静态资源与埋点 |
| 沉淀成资产 | 导出后手工补参数、断言与前置条件 |
| 做回归 | 交给 shenle-api-cli 的 send / assert |

示例：先看真实帮助，再抄参数，别凭记忆写子命令。

```bash
shenle-api-record --help
```
