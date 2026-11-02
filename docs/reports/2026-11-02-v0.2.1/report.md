# AI QA Lab 项目报告

> 日期：2026-11-02
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

## 3. 步骤

### 本地启动

```bash
cd /e/ailearning/ai-qa-lab
bash scripts/start_sut.sh
```

### 跑测试

```bash
./.venv/Scripts/python.exe -m pytest apps/sut/backend suites/api -q
```

### 验收页面

```
/ui/               仪表盘
/ui/#/tickets      工单管理
/ui/#/workbench    API 工作台
/ui/#/report       项目报告
/ui/#/portfolio    模块验收
```

### 容器部署

```bash
docker build -t ai-qa-lab .
docker run -p 8000:8000 ai-qa-lab
# Render Blueprint: render.yaml
```

## 4. 最后成果

- 33 个自动化测试全部通过
- 6 个前端页面，构建成功
- 8 个模块的 GitHub 最高星项目选型矩阵
- 1 个可运行的复刻闭环：模块 03 API 工作台
- 公开仓库、CI、验收截图、Docker/Render 部署配置

详细验收：

- `docs/portfolio/sut-console.md`
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
- 下一项：模块 02 迷你 pytest（收集、fixture、参数化、报告）。

## 7. 新手向完整拆解

面向测试小白的逐步讲解已单独成页，包含：每一步做了什么、为什么、涉及的名词、原理、效果；术语速查表；简历写法；面试追问；10 道自测题。

- 在线版：https://shenle2019.github.io/ai-qa-lab/learning/
- 源文件：`docs/learning/project-walkthrough.md`
