# ai-qa-lab 项目约定

## 项目目标
面向杭州 30K+ 测试开发（AI 质量方向）岗位的公开作品集。用一套可运行的被测系统（SUT）+ 分层测试套件 + 测试平台，覆盖 8 个模块：质量工程方法论、Python 测试开发、接口自动化、Web 自动化、App 自动化、性能测试、测试平台、Agent/大模型评测。

## 目录约定
- `apps/sut`：被测系统（FastAPI + Vue3 + SQLite），后端在 `apps/sut/backend`
- `apps/platform`：测试平台（FastAPI + Vue3 + Allure）
- `libs`：跨模块复用的 Python 库，不放业务应用
  - `libs/minipytest`：模块 02 的自研测试框架；包名不得为 `pytest`，不得覆盖真实 pytest
- `suites/api|web|app|perf|agent`：各层测试套件，按模块归档
- `docs/notes`：对外笔记，仓库是唯一信源
- `docs/portfolio`：作品集站点内容
- `docs/progress`：每日进度归档，文件名 `YYYY-MM-DD.md`
- `scripts`：本地脚本（启动、数据准备、报告汇总）
- `.github/workflows`：CI

## 技术栈
- Python 3.11：`C:\Users\Administrator\.claude\tools\python311\python.exe`
- 后端 FastAPI + SQLAlchemy + SQLite；前端 Vue3 + Vite（第 1 周加入）
- 测试 pytest + requests/httpx；Web 用 Playwright；App 用 Appium + 现成 AVD `Pixel_3a_API_36`；性能用 Locust
- 报告 Allure；CI 用 GitHub Actions

## 环境与命令（在仓库根目录执行）
- 建环境：`py -3.11 -m venv .venv`（便携版 `.claude\tools\python311` 缺 venv 模块，不能用它建环境）
- 装依赖：`.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
- 启动 SUT：`.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000 --reload`
- 跑测试：`.venv\Scripts\python.exe -m pytest apps/sut/backend -q`
- 框架元测试：`.venv\Scripts\python.exe -m pytest libs/minipytest/tests -q`
- 迷你 pytest 演示：`.venv\Scripts\python.exe -m libs.minipytest libs/minipytest/demo/acceptance -v`
- 所有虚拟环境和依赖放 E 盘，禁止装到 C 盘。

## 编码约定
- 代码、变量名、提交信息用英文；文档和笔记用中文。
- 新增功能必须带 pytest 用例；接口变更同步 OpenAPI 说明。
- 不在代码、日志、提交里出现密钥；密钥只放 `.env`，示例放 `.env.example`。
- 不注释掉报错、不加绕过标记；找根因。

## 每日工作流
1. 开工先读 `docs/progress/` 最新文件，确认当天任务。
2. 每个任务完成即跑验证，再写进度。
3. 每天结束前更新 `docs/progress/YYYY-MM-DD.md`。
4. 涉及 git push、公网部署、删除文件、改密钥，必须先问。

## 教学模式（2026-11-02 用户要求，长期有效）
每完成一项任务/模块，必须用测试小白能懂的语言解释：做了什么、为什么做、涉及的名词、原理、效果；同步写入 `docs/learning/` 和项目报告。不能只交付结果。

## 模块复刻规则（2026-11-02 新增，优先级高于普通实现）
每个模块必须先搜索该主题 GitHub star 最高的项目并记录项目、star、链接、许可证、选型理由；以它为基准复刻核心能力，不直接 fork/复制源码。复杂度下限是完整闭环（输入 → 执行 → 结果 → 可视化/报告），禁止 Hello World/纯 CRUD demo。每个模块必须交付：可运行代码、验收网页、原理说明、使用步骤、最终效果。详细规则见 `docs/requirements/2026-11-02-module-replication.md`。

## 完成标准（每个模块）
- 有可运行代码和自动化用例，本地一条命令跑通
- 有测试报告或截图
- 有 1 篇对外笔记（问题、方案、结果、踩坑）
- 能在 5 分钟内讲清架构、取舍和失败案例
