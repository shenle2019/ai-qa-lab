# 审计延后项（2026-11-04）

来源：全栈审计报告 38 项中未处理的 7 项。当前版本 v1.1.0 已完成安全止血，以下项按优先级排列。

## 1. PostgreSQL 迁移

- 前置：Railway 创建 PostgreSQL 实例，产生用量费用。
- 动作：`DATABASE_URL` 指向 Postgres；安装 `psycopg`；验证 SQLite 专用补丁（`_ensure_sqlite_int`）可删除。
- 验收：重新部署后数据不丢，多实例可写。

## 2. Alembic 迁移体系

- 前置：确认现有数据库基线。
- 动作：引入 Alembic，生成 baseline，给现有库 `stamp`；下线 `create_all` 与 `schema_migrations.ensure_columns`。
- 验收：空库可一键升级；升级/回滚命令可复现。

## 3. routers / services / repositories 三层重构

- 动作：按 feature 拆分 `platform_api.py`；路由只做参数校验与编排，业务进 services，查询进 repositories。
- 验收：路由文件不再出现 SQL 查询；服务层不依赖 FastAPI Request/Response。

## 4. JWT + User 表 + RBAC

- 动作：用户表、登录、短时 access + refresh、角色与权限；替换当前服务级 API Key。
- 验收：匿名写 401；普通用户不能访问管理端点；前端 401 自动刷新重试。

## 5. 全量 Pinia 状态收敛

- 动作：tickets 之外的 9 个视图统一进入 Pinia store，消除重复请求与状态双轨。
- 验收：同一数据多页面共享，切换页面不重复拉取。

## 6. ESLint / Prettier

- 动作：引入 ESLint（Vue 规则）与 Prettier，修正存量格式；CI 增加 lint。
- 验收：`npm run lint` 零错误，CI 阻断不合规提交。

## 7. 镜像非 root 与静态文档移出运行镜像

- 动作：创建非 root 用户并处理 `/app/data` 权限；学习页与展示页改由 GitHub Pages 提供，运行时镜像只保留 backend + frontend dist。
- 验收：容器以非 root 运行；镜像体积下降；`/learning`、`/portfolio` 链接仍可访问。

## 说明

当前 v1.1.0 的安全边界：写接口需要服务级 Key；读接口公开；生产关闭 API 文档；内网 SSRF 已拦截；LLM Key 只在服务端环境变量。
