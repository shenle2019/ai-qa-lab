# AI全栈测试开发平台-shenle 项目报告

> 日期：2026-11-03
> 仓库：https://github.com/shenle2019/ai-qa-lab
> 公网报告页：https://shenle2019.github.io/ai-qa-lab/

## 1. 我做了什么

| 时间 | 事项 | 产物 |
|---|---|---|
| 17:02 | 项目启动 | monorepo、CLAUDE.md、目录约定、Python 3.11 环境 |
| 17:10 | SUT 后端最小闭环 | FastAPI + SQLAlchemy + SQLite，健康检查、工单 CRUD、知识库 mock，6 个 pytest |
| 17:13 | 公开仓库与 CI | `shenle2019/ai-qa-lab`、GitHub Actions、SSH 443 推送 |
| 17:30 | 接口自动化 | `suites/api` 22 个黑盒用例 |
| 18:00 | 复刻规则与选型 | 8 模块最高星参考矩阵 |
| 18:20 | Vue 控制台 | 仪表盘、工单、知识库、API 工作台、项目报告、模块验收 |
| 18:40 | 模块 03 复刻 v0.1 | Hoppscotch 风格 API 工作台，5 个契约测试，全量 33 passed |
| 11-03 12:26 | 模块 02 复刻 v0.1 | 迷你 pytest：收集、fixture、参数化、marker、断言内省、重试、JSON/HTML 报告；33 元测试 + 20 演示 |
| 11-03 16:42 | 模块 04 复刻 v0.1 | 迷你 Playwright：CDP 驱动、选择器、自动等待、断言、截图；6 元测试 + 5 个 SUT UI 用例 |
| 11-03 16:48 | 模块 05 复刻 v0.1 | 迷你 Appium：ADB/UIAutomator、元素定位、点击、等待、截图；5 元测试 + 3 个 Settings 用例 |

## 2. 原理

```
Browser (Vue 3 SPA)
  ├─ 仪表盘 / 工单 / 知识库 / API 工作台 / 项目报告
  └─ fetch /api/*
        │
        ▼
FastAPI (apps/sut/backend)
  ├─ /health, /api/tickets, /api/kb/query
  ├─ /api/workbench/send, /api/workbench/run
  └─ /ui ← Vue 构建产物（同源托管）
        │
        ▼
SQLAlchemy → SQLite
```

- **统一被测系统**：前后端围绕同一套工单/知识库数据，接口测试与 UI 测试覆盖同一条链路。
- **分层测试**：后端冒烟、接口黑盒、工作台契约测试独立；测试库用临时 SQLite，数据随机后缀隔离。
- **API 工作台**：浏览器编辑请求，FastAPI 用 httpx 代理发送，解决 CORS，统一超时和断言求值。
- **复刻方法**：先搜同主题最高星项目，记录 star/license/链接，再 clean-room 重写核心闭环，不 fork、不复制源码。
- **同源部署**：前端构建产物由 FastAPI 在 `/ui` 挂载，生产环境只需要一个容器/端口。
- **Web 自动化**：miniplaywright 通过 Chrome DevTools Protocol 驱动 Edge/Chrome，不依赖 Playwright 库。
- **App 自动化**：miniappium 通过 ADB + UIAutomator 驱动 Android 模拟器，不依赖 Appium Server。

## 3. 步骤

### 本地启动

```bash
cd /e/ailearning/ai-qa-lab
bash scripts/start_sut.sh
```

### 跑测试

```bash
./.venv/Scripts/python.exe -m pytest apps/sut/backend suites/api libs/minipytest/tests libs/miniplaywright/tests libs/miniappium/tests -q
```

### 验收页面

```
/ui/               仪表盘
/ui/#/tickets      工单管理
/ui/#/workbench    API 工作台
/ui/#/report       项目报告
/ui/#/portfolio    模块验收
/portfolio/module-02-minipytest-report.html  模块 02 报告
```

### 容器部署

```bash
docker build -t ai-qa-lab .
docker run -p 8000:8000 ai-qa-lab
# Render Blueprint: render.yaml
```

## 4. 最后成果

- 77 个真实 pytest 用例全部通过（33 现有 + 33 迷你 pytest + 6 迷你 Playwright + 5 迷你 Appium）
- 28 个迷你演示用例：20 个迷你 pytest + 5 个迷你 Playwright + 3 个迷你 Appium
- 6 个前端页面，构建成功
- 8 个模块的 GitHub 最高星项目选型矩阵
- 4 个可运行的复刻闭环：模块 03 API 工作台、模块 02 迷你 pytest、模块 04 迷你 Playwright、模块 05 迷你 Appium
- 公开仓库、CI、验收截图、Docker/Render 部署配置

详细验收：

- `docs/portfolio/sut-console.md`
- `docs/portfolio/module-02-mini-pytest.md`
- `docs/portfolio/module-04-mini-playwright.md`
- `docs/portfolio/module-05-mini-appium.md`
- `docs/portfolio/module-03-api-workbench.md`
- `docs/requirements/module-matrix.md`

## 5. 能否在远端公网访问运行

**能。** 但要区分两层：

| 方式 | 能运行什么 | 账号 | 状态 |
|---|---|---|---|
| GitHub Pages | 项目报告、截图、文档 | 已有 GitHub | 本报告页公网可访问 |
| Render Docker | 完整 SUT + Vue + API 工作台 | Render 账号 | 配置已就绪，待授权 |
| Hugging Face Spaces | 完整 SUT + Vue + API 工作台 | HF 账号 | 备选 |
| 本地 | 全部功能 | 无 | 已运行 |

**当前决策：先本地开发，等 8 个模块全部完成后再统一上云。** 部署配置保留，不阻塞开发。

GitHub Pages 不能运行 Python 后端，所以完整可运行版本必须部署到容器平台。仓库已提供：

- `Dockerfile`：Node 构建前端 → Python 运行 FastAPI
- `render.yaml`：Render Docker Web Service，免费层，健康检查 `/health`
- `.dockerignore`：排除依赖、数据库、文档
- `SEED_DEMO=1`：首次启动自动写入演示工单

Render 一键部署入口：

```
https://render.com/deploy?repo=https://github.com/shenle2019/ai-qa-lab
```

## 6. 边界与下一步

- 没有登录/权限体系，模块 07 复刻 MeterSphere 时补。
- 知识库仍是 mock，模块 08 接入 DeepSeek + 真实检索与评测。
- API 工作台只做 REST，不做 GraphQL/WebSocket/请求链路变量提取。
- SQLite 适合演示，不适合多用户生产；后续切 PostgreSQL。
- 下一项：模块 06 性能测试（迷你压测引擎）。

## 7. 五个常见问题（2026-11-03）

### 7.1 学习页标题为什么改了

学习页原来叫 “AI QA Lab”，现在改成 “AI全栈测试开发平台-shenle”。改的是浏览器标签、页面顶部和一级标题，内容不变。控制台侧边栏也同步换成了这个显示名，仓库名 `ai-qa-lab` 没变。

### 7.2 SUT 在哪里，我能看见吗

SUT 就是被测系统（System Under Test）。代码在 `apps/sut/backend`（FastAPI + SQLite）和 `apps/sut/frontend`（Vue3）。启动后有两个入口：

- `http://127.0.0.1:8000/ui/`：用户界面，能看仪表盘、工单、知识库、API 工作台、报告、模块验收。
- `http://127.0.0.1:8000/docs`：接口文档，能直接点 “Try it out” 发请求。

现在实际有 8 个 HTTP 接口：健康检查、工单列表、创建工单、查单个工单、更新工单、知识库问答，加 2 个工作台接口。之前报告写 7 个，是旧口径，已更正。

### 7.3 模块 03 接口自动化是什么

参考 Hoppscotch（80,721 星），它是一个开源的 Postman 类 API 工具。我们没复制源码，只复刻核心闭环：发请求、环境变量、5 种断言、集合保存、批量运行、报告。入口是 `/ui/#/workbench`。

它解决的是“接口测试不只是发请求”，还要有环境、断言、批量、报告。v0.1 不做 GraphQL、WebSocket、脚本和团队协作。

### 7.4 模块 01 方法论是什么

参考 awesome-test-automation（7,208 星），它是一个测试工具清单和地图，不是可运行程序。我们用它来确定 8 个模块、每个模块的最高星参考项目和复刻规则。

产物是 `docs/requirements/module-matrix.md` 和 `CLAUDE.md` 里的规则：先选最高星项目、clean-room 复刻、完整闭环、验收页。模块 01 排在最后，因为它要把整个项目总结成知识地图和选型决策页。

### 7.5 模块 07 测试平台现在有什么

参考 MeterSphere（13,600 星），它是一个持续测试平台，管理项目、用例、计划、执行、缺陷、报表。现在有 Vue 控制台 + FastAPI 后端，能看仪表盘、工单、知识库、API 工作台、报告、模块验收，所以叫“控制台雏形”。

还缺用例管理、测试计划、执行历史、缺陷跟踪、权限和 CI 集成。这些是模块 07 要补的完整闭环。

## 8. 新手向完整拆解

面向测试小白的逐步讲解已单独成页，包含：每一步做了什么、为什么、涉及的名词、原理、效果；术语速查表；简历写法；面试追问；13 道自测题。

- 在线版：https://shenle2019.github.io/ai-qa-lab/learning/
- 源文件：`docs/learning/project-walkthrough.md`
