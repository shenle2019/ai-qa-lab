---
title: AI QA Lab
emoji: 🧪
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# AI QA Lab

AI 全栈测试工程项目：FastAPI + Vue 3 + SQLite，内含 SUT 控制台、API 工作台、自动化测试与项目报告。

- 源码：https://github.com/shenle2019/ai-qa-lab
- 报告：https://shenle2019.github.io/ai-qa-lab/
- 技术栈：FastAPI、SQLAlchemy、SQLite、Vue 3、Vite、Pinia、ECharts

Docker Space 会自动克隆 GitHub 仓库、构建前端并启动 FastAPI。演示数据由 `SEED_DEMO=1` 首次启动写入。

注意：SQLite 存储在 Space 的临时磁盘，重启后会重置，适合演示环境。
