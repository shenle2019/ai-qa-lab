# ai-qa-lab

AI-powered full-stack QA portfolio. One runnable system under test (SUT), layered test suites, and a test platform — built module by module.

面向 AI 时代的全栈测试开发作品集：一套可运行的被测系统、分层测试套件与测试平台，覆盖接口、Web、App、性能与 Agent/大模型评测。

## Status

| Module | Status |
|---|---|
| 01 质量工程方法论 | planned |
| 02 Python 测试开发 | planned |
| 03 接口自动化 | planned |
| 04 Web 自动化 | planned |
| 05 App 自动化 | planned |
| 06 性能测试 | planned |
| 07 测试平台 | planned |
| 08 Agent / LLM 评测 | planned |

## Structure

```
apps/sut        System under test (FastAPI + Vue3 + SQLite)
apps/platform   Test platform (FastAPI + Vue3 + Allure)
suites/         Layered test suites: api, web, app, perf, agent
docs/notes      Public notes (single source of truth)
docs/portfolio  Portfolio site content
docs/progress   Daily progress log
```

## Quick start

```bash
# Python 3.11 (portable)
C:\Users\Administrator\.claude\tools\python311\python.exe -m venv .venv

# Dependencies (Tsinghua mirror)
.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Run SUT
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000 --reload

# Tests
.venv\Scripts\python.exe -m pytest apps/sut/backend -q
```

API docs: http://127.0.0.1:8000/docs

## License

MIT
