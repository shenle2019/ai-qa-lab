# v1.1.0 · 安全加固与审计修复

日期：2026-11-04
类型：安全与工程加固
基线：v1.0.0

## 这个版本做了什么

根据全栈审计报告（38 项），完成 P0 安全问题与大部分 P1/P2/P3 工程问题：

- 生产环境写接口改为服务级访问密钥认证；前端新增“访问密钥”页与 401 跳转。
- LLM Key 只从环境变量读取，数据库不再保存明文；线上移除 DeepSeek 变量。
- SSRF 校验：DNS 解析、拒绝私网/回环/link-local/保留段、禁止跟随重定向、批量上限 10。
- 生产关闭 `/docs`、`/redoc`、`/openapi.json`；移除镜像内 `SEED_DEMO`。
- request-id、JSON 日志、全局异常兜底、安全响应头、显式 CORS、`/ready`、LLM 限流。
- 列表分页、executions N+1 修复、汇总口径改为最近 10 次。
- 执行改为 202 + BackgroundTasks，前端轮询；生产禁用客户端上报结果的 `/run`。
- 工单支持编辑；知识库改为真实词法检索并返回来源。
- 前端路由懒加载、echarts 动态导入、fetch 超时/重试/401、错误中文化、健康检查轮询。
- 依赖拆分、临时文件清理、部署配置归档、CI 增加前端与镜像构建、Docker 健康检查。

## 验证

- 全量 pytest：351 passed，42 skipped（跳过均为无 Android 设备）。
- 线上：匿名写请求 401；带密钥写请求 201；`/docs` 与 `/openapi.json` 404；内网 SSRF 400；安全头存在。
- 测试用例目录：196 条，183 通过，13 跳过。

## 延后项

7 项需要新基础设施或大重构，已记录在 `docs/requirements/audit-backlog.md`：

PostgreSQL、Alembic、完整三层重构、JWT/RBAC、全量 Pinia、ESLint/Prettier、镜像非 root 与静态文档移出镜像。
