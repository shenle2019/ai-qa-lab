# ai-qa-lab

AI-powered full-stack QA test platform. One runnable system under test (SUT), layered test suites, and a test platform — built module by module.

面向 AI 时代的全栈测试开发项目：一套可运行的被测系统、分层测试套件与测试平台，覆盖接口、Web、App、性能与 Agent/大模型评测。

## Status

| Module | Status |
|---|---|
| 01 质量工程方法论 | done (v0.1) — methodology page |
| 02 Python 测试开发 | done (v0.1) — minipytest + 33 meta tests + 20 demo cases |
| 03 接口自动化 | done (v0.1) — API Workbench + 56 tests |
| 04 Web 自动化 | done (v0.1) — miniplaywright + 6 meta tests + 5 SUT UI cases |
| 05 App 自动化 | done (v0.1) — miniappium + 5 meta tests + 3 Settings cases |
| 06 性能测试 | done (v0.1) — miniload + 5 meta tests + SUT load run |
| 07 测试平台 | done (v0.1) — projects/cases/plans/executions/defects; AI generation + review gate + real execution |
| 08 Agent / LLM 评测 | done (v0.1) — minieval + 5 meta tests + 5-case dataset |

## Platform capabilities

- Model center: register OpenAI-compatible models, mask API keys, test connectivity, and record every call with latency and token usage.
- AI case generation: turn a requirement into structured draft cases, including executable step JSON.
- Review gate: draft → pending review → approved or rejected; only approved cases can be executed.
- Real execution: the server runs approved API cases step by step against a configurable base URL and stores per-case results.
- Execution report: every run has a standalone HTML report with pass rate and failure reasons.


## Test catalog

Every suite is browsable in the running app at `/ui/#/testcases`.

| Category | Cases |
|---|---:|
| API techniques | 51 |
| Compatibility | 35 |
| Reliability | 26 |
| Web UI | 30 |
| Performance | 29 |
| App | 25 |

- 196 cases total: 183 passed, 13 skipped because no Android device is attached.
- Filter by category, status, or name; the page reads `/portfolio/test-cases.json`, generated from the same JUnit run as the report.
- Regenerate with `.venv/Scripts/python.exe scripts/build_test_report_2026_11_04.py`.
- Full report: `/portfolio/test-report-2026-11-04.html`.

## Structure

```
apps/sut        System under test (FastAPI + Vue3 + SQLite)
apps/platform   Test platform (FastAPI + Vue3 + Allure)
libs/minipytest Module 02 clean-room pytest-like runner + demo suites
libs/miniplaywright Module 04 CDP browser automation + demo suite
libs/miniappium   Module 05 ADB/UIAutomator Android automation + demo suite
libs/miniload     Module 06 threaded load engine + HTML report
libs/minieval     Module 08 LLM evaluation engine + dataset + report
suites/         Layered test suites: api, web, app, perf, agent
docs/notes      Public notes (single source of truth)
docs/portfolio  Project showcase content
docs/progress   Daily progress log
```

## Quick start

```bash
# Python 3.11 (workbuddy install; the portable .claude\tools copy lacks venv)
py -3.11 -m venv .venv

# Dependencies (Tsinghua mirror)
.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Frontend build
cd apps/sut/frontend
npm install
npm run build
cd ../../..

# Run SUT (serves API + UI)
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/sut/backend --port 8000 --reload

# Tests (393 real pytest cases, Android device tests skip automatically)
.venv\Scripts\python.exe -m pytest apps/sut/backend suites/api suites/web suites/app suites/perf libs/minipytest/tests libs/miniplaywright/tests libs/miniappium/tests libs/miniload/tests libs/minieval/tests -q

# Mini pytest acceptance demo (20 cases, starts a temporary SUT)
.venv\Scripts\python.exe -m libs.minipytest libs/minipytest/demo/acceptance -v \
  --json docs/portfolio/module-02-minipytest-report.json \
  --html docs/portfolio/module-02-minipytest-report.html
```

- UI: http://127.0.0.1:8000/ui/
- API docs: http://127.0.0.1:8000/docs
- Project report: `/ui/#/report` (local) · https://shenle2019.github.io/ai-qa-lab/ (public)

## Report archive

- **Learning guide (beginner-friendly): https://shenle2019.github.io/ai-qa-lab/learning/**
- Latest report: https://shenle2019.github.io/ai-qa-lab/
- Archive index: https://shenle2019.github.io/ai-qa-lab/reports/
- **2026-11-05 tester-skills snapshot: https://shenle2019.github.io/ai-qa-lab/reports/2026-11-05-tester-skills/** — SeaZhusp/tester-skills 对 SUT 的接口自动化测试（39 接口 → 35 条生成用例；修正版 29/29 通过）
- Rule: daily logs live in `docs/progress/`; milestone reports are immutable snapshots in `docs/reports/YYYY-MM-DD-vX.Y.Z/` (see `docs/reports/README.md`).
- Create a snapshot:

```bash
.venv/Scripts/python.exe scripts/archive_report.py \
  --version v0.3.0 --date 2026-11-03 \
  --tests 40 --pages 6 --modules 8 --replications 2
```

## Deploy

Railway is the single maintained deployment target.

- Live demo: https://ai-qa-lab-production.up.railway.app/ui/
- Build: `docker build -t ai-qa-lab .`
- Environment variables:
  - `APP_ENV=production`
  - `APP_API_KEY=<write access key>` — required; write requests use `Authorization: Bearer <key>` or `X-API-Key`
  - `DATABASE_URL=sqlite:////app/data/sut.db`
  - `DEEPSEEK_API_KEY` — optional, only needed for AI case generation
  - `SEED_DEMO=1` — local only, never set in production
- Mount a persistent volume at `/app/data`.
- In production `/docs`, `/redoc` and `/openapi.json` are disabled.
- The UI includes an “访问密钥” page that stores the key in browser localStorage; 401 responses redirect there.
- Render and Hugging Face configs are archived under `docs/archive/deploy/` and are not maintained.

## License

MIT
