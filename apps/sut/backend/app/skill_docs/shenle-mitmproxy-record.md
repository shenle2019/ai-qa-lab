---
name: shenle-mitmproxy-record
description: "使用场景：用 mitmproxy 代理录制 HTTP/HTTPS 流量，产出可归档的请求清单（.json）与接口资产，供接口文档与用例生成使用。当用户说「录一下流量」「抓包归档」时触发。"
version: 0.1.0
---
重点：请使用中文沟通！！

# ⚠️ 检测录制结果时，禁止用 Read 工具直接打开 raw{NN}.json

raw 文件可能很大（一次录制常常几百 KB ~ 几 MB），里面 cookies、headers、body 都会占满上下文。**录制结束后一律调用 `scripts/inspect_recording.py` 拿摘要**，不要用 Read / Grep 去看 raw 文件的具体内容。

# shenle Mitmproxy Record

shenle mitmproxy 网络录制工具 — 通过系统代理录制桌面应用 / APP / 手机 H5 的 HTTP/HTTPS 流量，输出与 `shenle-api-record` 完全兼容的 `raw{NN}.json`。

## 使用场景

- **桌面应用录制**：采集 Electron / Qt / .NET / Java Swing 等桌面软件的网络请求
- **手机 H5 / APP 录制**：手机 Wi-Fi 设置代理到电脑 IP，录制所有 HTTP/HTTPS 请求
- **任意 HTTP 客户端抓包**：CLI 工具、SDK、爬虫等
- **HTTPS 透明解密**：mitmproxy 用 CA 伪造证书实现解密，自动安装到系统根证书库
- **Web 页面只抓业务接口**：配 `--resource-filter api-only`，自动跳过 HTML 页面、css/js/png/字体/视频 等静态资源

**不适用**：
- 纯 Web SPA 抓 XHR → 用 `shenle-api-record`（Playwright CDP，更精准；按需选 mitmproxy + `--resource-filter api-only` 也行）
- 要 DOM/截图 → 用 `shenle-web-record`
- PC 桌面画面采集 → 用 `shenle-pc-record`

## Usage

```bash
# 主流程：启动录制（默认打开 mitmweb Web UI + 引导浏览器）
shenle-mitmproxy-record record

# 桌面应用 / APP：不打开引导浏览器
shenle-mitmproxy-record record --no-browser

# 自定义端口
shenle-mitmproxy-record record --port 8888 --web-port 8889

# 指定输出目录（注意！除非用户明确指定，否则使用默认输出地址）
shenle-mitmproxy-record record --no-browser --output ./output

# 仅安装 CA 证书
shenle-mitmproxy-record install-ca

# 环境检查
shenle-mitmproxy-record check

# 停止后台录制
shenle-mitmproxy-record stop

# 帮助信息
shenle-mitmproxy-record --help
```

## 录制流程

1. 运行 `shenle-mitmproxy-record record`，CLI 自动检查并按需 `pip install mitmproxy`（清华源）
2. **首次运行**会触发 CA 证书生成 + 尝试安装到系统证书库（需管理员/root 一次）
3. **控制面板**自动打开（`http://127.0.0.1:9090/`，含 mitmweb UI + 右下角"🛑 停止录制"浮动按钮）
4. 客户端配置代理 `127.0.0.1:8080`：
   - **浏览器**：设置 → 系统代理（或浏览器扩展 SwitchyOmega）
   - **手机 H5**：Wi-Fi 设置 → 手动代理 → IP 填电脑内网 IP，端口 8080
   - **桌面应用**：应用网络设置 → 代理 `127.0.0.1:8080`
5. 正常使用客户端，所有 HTTP/HTTPS 请求被录制到 `./AI-信息采集/<批次号>/raw{NN}.json`
6. **点击页面右下角"🛑 停止录制"按钮** = 优雅停止录制并保存 raw 文件（或 Ctrl+C）

## 输出文件

接口采集统一命名 `AI-信息采集`，**不分模块**，按批次号(日期-序号)直接组织。

- **位置**：`{output}/<批次号>/`
- **格式**：`raw{NN}.json`（按录制顺序编号）
- **内容**：请求方法、URL、请求头、请求体、响应状态码、响应体
- **二进制 body**：`"base64:<...>"` 前缀 + base64 编码

完整目录示意（项目根下三个统一根目录并列）：

```text
<project-root>/
├── AI-信息采集/                    ← --output 默认值
│   └── 2026-07-28-153012/         ← 批次号(YYYYMMDD-HHMMSS)
│       ├── raw01.json
│       ├── raw02.json
│       └── mitmweb.log            ← mitmweb 运行日志
├── AI-接口管理/                    ← 接口文档根（doc-generator）
└── AI-测试用例/                    ← 接口用例根（case-generator）
```

每条记录结构（与 shenle-api-record 完全一致）：

```json
{
  "request": {
    "id": "140234567890123",
    "method": "POST",
    "url": "https://api.example.com/login",
    "headers": {"Content-Type": "application/json", ...},
    "body": "{\"username\":\"admin\"}",
    "timestamp": 1690453812.345
  },
  "response": {
    "status": 200,
    "headers": {"Content-Type": "application/json", ...},
    "body": "{\"token\":\"abc123\"}",
    "timestamp": 1690453812.678
  }
}
```

## 检测录制结果

录制完成后**不要**用 Read 打开 raw 文件查看内容。直接调用检测脚本：

```bash
# 方式 1：传具体文件
python .claude/skills/shenle-mitmproxy-record/scripts/inspect_recording.py \
  AI-信息采集/2026-07-28-153012/raw01.json

# 方式 2：传目录
python .claude/skills/shenle-mitmproxy-record/scripts/inspect_recording.py \
  AI-信息采集/2026-07-28-153012/

# 方式 3：不传参，默认扫描 ./AI-信息采集/
python .claude/skills/shenle-mitmproxy-record/scripts/inspect_recording.py
```

脚本输出：每个文件的接口数 + `[方法] [状态码] URL` 列表 + 按方法/状态的汇总。**只看摘要，不要继续深入 body 内容。**

## 参数说明

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--port` | mitmproxy 代理端口（客户端指向这里） | `8080` |
| `--web-port` | mitmweb Web UI 端口（原始入口） | `8081` |
| `--control-port` | **控制面板端口**（推荐访问这个，含"🛑 停止录制"按钮） | `9090` |
| `--output`, `-o` | 输出根目录（**除非用户明确指定，否则不要配置**） | `./AI-信息采集` |
| `--no-browser` | 不打开引导浏览器（APP/桌面应用） | 关闭 |
| `--skip-ca-install` | 跳过 CA 安装（已手动装好时） | 关闭 |
| `--no-stop-on-ui-close` | 关闭 UI 也不停止（手动 Ctrl+C） | 关闭 |
| `--ui-timeout` | UI 不可用 N 秒后停止（0=不限） | `0` |
| `--exclude-pattern` | 排除的 URL 正则（可多次） | - |
| `--include-pattern` | 白名单正则 | - |
| `--resource-filter` | 资源过滤预设：`off`（默认）/ `static`（跳静态资源）/ `api-only`（仅保留 AJAX） | `off` |
| `--auto-split-by-domain` | 按 host 自动分文件 | 关闭 |
| `--raw-index-start` | raw 文件起始编号 | `1` |

## 环境要求

- **Python 3.9+**
- **mitmproxy 10.0+**（自动 pip install）
- **管理员/root 权限**（仅首次安装 CA 时需要）
- **客户端需支持 HTTP 代理配置**（手机需在同一局域网）
- 客户端系统需信任 mitmproxy CA 证书（移动设备首次访问 `http://mitm.it` 下载证书并信任）

## 工作原理

- mitmproxy 作为**中间人代理**：客户端 ↔ mitmproxy ↔ 真实服务器
- HTTPS 通过 mitmproxy 的 CA 伪造证书实现透明解密（addon 拿到的 `flow.request.pretty_url` 已是 `https://...`）
- mitmweb 内置 Web UI（端口 8081）提供实时查看/拦截
- addon `RecorderAddon` 订阅每个 HTTPFlow，转 dict 写入 `raw{NN}.json`
- 关闭 Web UI = mitmweb 主进程退出 = CLI 主循环结束

## 录制结束后的标准流程

1. CLI 退出后，确认 `./AI-信息采集/<批次号>/` 下生成了 `raw{NN}.json`
2. **运行检测脚本** `scripts/inspect_recording.py` 拿接口清单和数量
3. 告诉用户：录制文件路径、接口总数、按方法的分布
4. 询问用户下一步：继续追加录制 / 生成接口文档 / 生成测试用例

## ⚠️ 已知问题与排查清单

### 录制后 raw 文件为空（最常见）

按概率排序：

1. **`flush_threshold` 历史默认值 10**：录 < 10 条请求时未写盘（已修复，默认改为 1）。
   验证：手动 `curl -x http://127.0.0.1:8080 <API>` 看是否有 raw 文件生成。
2. **api-only 过滤过严**：HTML 页面、图标、字体等被丢弃是预期行为，但用户误以为"应该被录制"。
   验证：用 `curl -I` 看响应 `Content-Type`，必须含 json/xml/form/text/plain/javascript 才落盘。
3. **请求没到 mitmproxy**：手机代理配错、IP/端口不通、APP 启用了 SSL Pinning。
   验证：手机浏览器访问 `http://<电脑IP>:8080/` 看控制面板能否打开；APP 内是否有请求。
4. **addon 没加载**：addon_entry.py 路径错、Python 环境不一致（shenle-mitmproxy-record 装在 Py3.9、mitmweb 在 Py3.11）。
   验证：mitmweb.log 应包含 `[shenle-mitmproxy-record] addon running`。
5. **停止时 `done()` 未触发**：mitmweb 子进程被 SIGKILL 强杀，跳过 `done()` 钩子 → 未调用 `flush_pending()`。
   验证：先在控制面板点 🛑 优雅停止（关闭 Web UI 即可），不要直接 `taskkill /F`。

## 与其他录制工具的区别

| 工具 | 适用场景 | 抓取方式 |
| --- | --- | --- |
| `shenle-api-record` | Web SPA（XHR/Fetch） | Playwright CDP，浏览器内拦截 |
| `shenle-web-record` | Web 页面（含 DOM/截图） | Playwright CDP，全网络 |
| `shenle-mitmproxy-record` | 桌面/APP/手机 H5 | **mitmproxy 系统代理** |

<!-- hardened:six-shapes -->
动手前 MANDATORY 先读 references/record-checklist.md（证书、filter、脱敏三步的自检单）。

## 执行顺序

1. 先确认录制目标（App / Web / 小程序）与代理方式，证书没装好先装。
2. 再起 mitmproxy 与客户端代理，只录目标域名，别把所有流量都存下来。
3. 然后操作被测流程，一次只跑一条业务链路，跑完就停。
4. 接着导出：按接口聚合，产出请求清单 JSON，敏感头做脱敏。
5. 最后自检：清单里没有 token、没有手机号明文，条目数与操作步数对得上。

## 判断与选择

| 情形 | 选哪条 | 为什么 |
| --- | --- | --- |
| HTTPS 抓不到 | 先查证书信任 | 90% 的抓不到都是证书问题 |
| 只关心某域名 | 用 filter 限定 | 全量录制会让清单不可用 |
| 有加密体 | 只录密文并标注 | 解密需要密钥，不在录制范围 |
| 多端并行 | 分端口分实例 | 混在一起分不清来源 |
| 要复现某请求 | 导出为可重放格式 | 只存原始流量后续难用 |

## 反模式

- **NEVER** 把带 token 的原始流量提交进仓库 —— 因为等于泄露账号。
- **NEVER** 录制时跑多个业务链路 —— 因为清单条目无法归因。
- **NEVER** 忽略证书错误继续录 —— 因为看到的可能是不完整流量。
- **NEVER** 只存 pcap 不存结构化清单 —— 因为下游无法直接消费。
- **NEVER** 在生产环境长时间挂着代理 —— 因为会影响别人排障。
- **NEVER** 录完不校验条数 —— 因为漏录比录错更难发现。

## 失败兜底

- 证书装不上：退回支持明文的环境录制，并在清单里标注来源。
- 录制中断：保留已完成部分，重录只补缺失链路。
- 脱敏遗漏：导出脚本二次扫描 token / 手机号 / 身份证模式，命中就失败。

## 一页速查

| 问题 | 怎么做 |
| --- | --- |
| 抓不到 HTTPS | 查证书 |
| 只录某站 | filter 限定 |
| 加密体 | 记密文 + 标注意 |
| 脱敏 | 导出时扫描替换 |
| 判断条目够不够 | 与操作步数对照 |
| 多端 | 分实例 |
| 交付前查什么 | 无明文密钥 |

## 示例

```bash
# 只录目标域名
mitmdump -p 8080 --set save_stream_file=capture/session.flow -f "~d example.com"

# 导出结构化清单并脱敏
python scripts/flow_to_list.py capture/session.flow --out capture/requests.json --mask
```
