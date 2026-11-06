# 部署与同步（Railway）

本仓库推送到 `main` 后由 Railway 自动构建（`Dockerfile` 多阶段：Node 构建前端 → Python 运行后端），线上地址：

- 平台 UI：<https://ai-qa-lab-production.up.railway.app/ui/#/>
- 健康检查：<https://ai-qa-lab-production.up.railway.app/health>
- OpenAPI（默认开发模式开启）：<https://ai-qa-lab-production.up.railway.app/docs>

## 部署方式（重要）

Railway **没有**接 GitHub 自动部署：`git push` 只更新源码，线上不会自动重建。实测 2026-11-06 推送后 10 分钟线上仍是 11-05 的镜像（`/health` 缺少 `auth` 字段）。

部署要显式执行：

```powershell
# CLI 已装在 E 盘，不与项目依赖混在一起
E:\ailearning\tools\railway\node_modules\.bin\railway.cmd up --ci
```

- 第一次需要登录：`railway login`（本机已登录 `shenle / 305030951@qq.com`，项目链接记录在 `~/.railway/config.json`）。
- `railway up` 会用仓库里的 `Dockerfile` 在云端构建并替换线上实例。
- 上传会遵循 `.gitignore`，所以 `.venv/`、`.pw-browsers/`、`node_modules/`、`data/` 不会被打包。

## 构建链

```text
node:24-alpine  → npm ci + npm run build → dist/
python:3.11-slim → pip install -r requirements.txt
                 → COPY apps/sut/backend, docs/learning, docs/portfolio, dist
                 → uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## 部署前必须满足

1. `requirements.txt` 覆盖代码实际依赖（`python-dotenv`、`python-multipart`、`PyYAML`），否则容器启动即崩。
2. `apps/sut/frontend/package-lock.json` 与 `package.json` 同步，`npm ci` 才过。
3. 环境变量在 Railway 面板配置（**不要**提交 `.env`）：
   - `APP_API_KEY`：访问密钥（生产模式下所有 `/api/*` 需带 `X-API-Key`）
   - `DEEPSEEK_API_KEY`：AI 能力所需的模型密钥
   - `APP_ENV=production`：关闭 `/docs` 并启用鉴权
4. 数据库默认是容器内 SQLite（`sut.db`），**重新部署会丢数据**。需要持久化时挂载 Railway Volume 并把 `DATABASE_URL` 指到该路径。

## 部署后自检

```powershell
python scripts\verify_production.py
```

脚本会校验：

- `/health` 含 `auth` / `docs` / `ui_automation` 三个字段（旧镜像没有）
- `/api/platform/skills` 返回 19 个 skill
- `/api/platform/environments`、`/api/platform/summary`、`/api/platform/ui-cases` 均 200
- `/ui/` 返回构建后的 SPA

UI 层再做一次真浏览器检查：

```powershell
python scripts\verify_production_ui.py   # 截图 5 个页面，统计 console error
```

## 2026-11-06 同步记录

| 项 | 结果 |
| --- | --- |
| GitHub | `60732d1` + `7518f6a` 已推 `main` |
| Railway | `railway up --ci` 部署成功 |
| `/health` | `auth=production`、`docs=false`、`ui_automation=false` |
| skill 数 | 19 |
| 生产 UI | 5 个页面渲染正常，0 console error；「API 文档」按 `docs=false` 自动隐藏；UI 自动化页显示浏览器缺失提示 |

## 已知的生产差异

- **UI 自动化**运行需要 Playwright + Chromium，镜像未安装（体积与构建风险）。`/health.ui_automation` 会返回 `false`，页面顶部给出提示；接口类与 AI 能力不受影响。要在生产启用，需在 `Dockerfile` 里加 `pip install playwright && playwright install --with-deps chromium`。
- **鉴权**：`APP_ENV=production` 时若配置了 `APP_API_KEY`，所有 `/api/*` 需带 `X-API-Key`；未配置则等同开放（当前线上即此状态）。
- **数据库**：容器内 SQLite。当前线上的 7 个项目/14 条用例在多轮部署后仍在，但**没有挂载 Volume**，一旦实例重建仍可能丢数据；重要数据请先导出或补 Volume。
