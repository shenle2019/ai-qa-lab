# v1.1.0 安全加固报告

> 日期：2026-11-04
> 基线：v1.0.0
> 审计来源：全栈审计报告（38 项）
> 处理结果：31 项已处理（含 4 项部分处理），7 项延后

## 一、P0 安全

| 审计项 | 处理 |
|---|---|
| 全站零认证 | 生产环境下所有 `/api/*` 非 GET 请求必须带 `Authorization: Bearer` 或 `X-API-Key`；缺失或错误返回 401。前端新增访问密钥页，401 自动跳转。 |
| DeepSeek Key 可被白嫖 | Key 只从环境变量读取，数据库不存明文；LLM 端点按 IP 限流；Railway 已删除 DeepSeek 变量。 |
| Workbench SSRF | URL 解析后做 DNS 解析，拒绝私网、回环、link-local、保留段、组播与 metadata 地址；不跟随重定向；批量子请求上限 10，超时上限 10 秒。 |
| SQLite + 临时盘 | 已使用 Railway 持久卷 `/app/data`，`DATABASE_URL=sqlite:////app/data/sut.db`；镜像不再硬编码 `SEED_DEMO`。PostgreSQL 迁移延后。 |
| docs/openapi 暴露 | 生产环境关闭 `/docs`、`/redoc`、`/openapi.json`。 |

## 二、P1 架构

- `get_db` 收敛到 `deps.py`，消除三处重复。
- 全局异常兜底、request-id、JSON 日志、CORS、安全响应头、`/ready`、限流。
- 执行改为 202 + BackgroundTasks + 前端轮询，避免单个 HTTP 请求挂 12 分钟。
- 生产禁用客户端上报结果的 `/run`；导入仍保留但需要认证。
- 列表分页；executions 列表一次预取 results，消除 N+1。
- Model Key 不再入库，展示口径统一为 `env:DEEPSEEK_API_KEY`。

## 三、P2 代码

- LLM 调用记账使用独立 Session，不再穿插业务事务。
- 超大 ID 返回 422；重名项目返回 200；时间统一走 `utcnow()` helper。
- 汇总通过率改为最近 10 次执行聚合。
- 知识库改为工单 + 内置知识的词法检索，返回真实来源。
- 工单 PATCH 支持标题、描述；前端增加编辑弹窗。
- 导入计划名加随机后缀；长消息截断加省略号。
- 前端：路由懒加载、echarts 动态导入、fetch 超时/GET 重试/401、错误中文映射、30 秒健康轮询、`VITE_API_BASE`。

## 四、P3 工程

- 删除 `_tmp_window*.xml`；旧报表脚本与 Render/HF 配置归档到 `docs/archive/`。
- `requirements.txt` 只保留运行时依赖，新增 `requirements-dev.txt`。
- Docker 增加 `HEALTHCHECK`；CI 增加前端构建与镜像构建。
- 新增 CSP、X-Frame-Options、nosniff、Referrer-Policy、HSTS。
- 测试新增安全用例：生产 401、缺服务端 Key 失败关闭、SSRF 私网拦截、安全头、`/ready`。

## 五、未完成与原因

| 项 | 原因 |
|---|---|
| PostgreSQL | 需要 Railway 数据库实例，涉及费用与数据迁移 |
| Alembic | 需要基线迁移与现有库 stamp，属于下一阶段 |
| 完整 routers/services/repositories | 大重构，当前只收敛了依赖 |
| JWT + User + RBAC | 当前是服务级 Key，用户体系需要独立设计 |
| 全量 Pinia | 涉及 10+ 视图状态改造 |
| ESLint/Prettier | 工具链引入与存量格式修正 |
| 镜像非 root / 文档移出镜像 | 与持久卷权限、静态页访问耦合，需单独验证 |

## 六、验证记录

- 全量 pytest：351 passed，42 skipped。
- 线上匿名写：401；带 Key 写：201；删除：204。
- `/docs`、`/openapi.json`：404。
- `http://127.0.0.1:8000/health` 经 Workbench：400。
- 安全头：`X-Request-ID`、`X-Frame-Options: DENY`、CSP 均存在。
- 用例目录：196 条，183 通过，13 跳过。
