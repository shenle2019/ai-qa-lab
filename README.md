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
| 07 测试平台 | done (v0.1) — projects/cases/plans/executions/defects |
| 08 Agent / LLM 评测 | done (v0.1) — minieval + 5 meta tests + 5-case dataset |

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

# Tests (172 real pytest cases)
.venv\Scripts\python.exe -m pytest apps/sut/backend suites/api libs/minipytest/tests libs/miniplaywright/tests libs/miniappium/tests libs/miniload/tests libs/minieval/tests -q

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
- Rule: daily logs live in `docs/progress/`; milestone reports are immutable snapshots in `docs/reports/YYYY-MM-DD-vX.Y.Z/` (see `docs/reports/README.md`).
- Create a snapshot:

```bash
.venv/Scripts/python.exe scripts/archive_report.py \
  --version v0.3.0 --date 2026-11-03 \
  --tests 40 --pages 6 --modules 8 --replications 2
```

## Deploy

> Status: all 8 modules are complete (v0.1) and archived as v1.0.0. The static report site is live; the full FastAPI + Vue app is deployment-ready and needs a Render/HF account authorization.

Full-stack (FastAPI + Vue) runs in one container:

```bash
docker build -t ai-qa-lab .
docker run -p 8000:8000 ai-qa-lab
```

Render Blueprint is included in `render.yaml`. One-click:

https://render.com/deploy?repo=https://github.com/shenle2019/ai-qa-lab

GitHub Pages only hosts the static report under `docs/`; it cannot run the Python backend.

### Hugging Face Spaces

The Space files are in `deploy/huggingface/` (README metadata + Dockerfile). The Dockerfile clones this public repo at build time, builds the Vue frontend, and starts FastAPI on port 7860.

**Web UI (no token needed):**

1. Open https://huggingface.co/new-space
2. SDK: Docker, template: Blank, name: `ai-qa-lab`, visibility: Public
3. Replace the Space `README.md` with `deploy/huggingface/README.md`
4. Add `deploy/huggingface/Dockerfile` at the Space root
5. Commit; the Space builds automatically
6. App URL: `https://<username>-ai-qa-lab.hf.space`

**Automated (recommended):**

```bash
.venv/Scripts/python.exe -m pip install -r requirements-deploy.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
# put a HF write token in .hf_token (never commit it)
.venv/Scripts/python.exe scripts/deploy_hf.py
```

The script creates the Space, uploads the two files, and prints the public URL. After pushing new commits to GitHub, use "Factory rebuild" in the Space settings to pick them up.

## License

MIT
