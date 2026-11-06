# 部署与同步（Railway）

本仓库推送到 `main` 后由 Railway 自动构建（`Dockerfile` 多阶段：Node 构建前端 → Python 运行后端），线上地址：

- 平台 UI：<https://ai-qa-lab-production.up.railway.app/ui/#/>
- 健康检查：<https://ai-qa-lab-production.up.railway.app/health>
- OpenAPI（默认开发模式开启）：<https://ai-qa-lab-production.up.railway.app/docs>

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

## 已知的生产差异

- **UI 自动化**运行需要 Playwright + Chromium，镜像未安装（体积与构建风险）。`/health.ui_automation` 会返回 `false`，页面顶部给出提示；接口类与 AI 能力不受影响。
- SQLite 无持久卷时，重启回到空库（首次访问可 `POST /api/platform/seed` 灌演示数据）。
