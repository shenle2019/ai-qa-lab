# ai-qa-lab

AI-powered full-stack QA portfolio. One runnable system under test (SUT), layered test suites, and a test platform — built module by module.

面向 AI 时代的全栈测试开发作品集：一套可运行的被测系统、分层测试套件与测试平台，覆盖接口、Web、App、性能与 Agent/大模型评测。

## Status

| Module | Status |
|---|---|
| 01 质量工程方法论 | planned |
| 02 Python 测试开发 | planned |
| 03 接口自动化 | in progress — API Workbench v0.1 + 33 tests |
| 07 测试平台 | in progress — SUT console live at /ui/ |
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

# Tests
.venv\Scripts\python.exe -m pytest apps/sut/backend suites/api -q
```

- UI: http://127.0.0.1:8000/ui/
- API docs: http://127.0.0.1:8000/docs
- Project report: `/ui/#/report` (local) · https://shenle2019.github.io/ai-qa-lab/ (public)

## Report archive

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

> Status: deployment is deferred until all 8 modules are complete. Local-first for now; Docker / Render / HF configs are kept for later.

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
