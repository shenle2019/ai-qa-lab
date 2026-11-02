#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -d .venv ]; then
  py -3.11 -m venv .venv
fi

./.venv/Scripts/python.exe -m pip install --disable-pip-version-check -q \
  -r requirements.txt \
  -i https://pypi.tuna.tsinghua.edu.cn/simple

cd apps/sut/frontend
if [ ! -d node_modules ]; then
  npm install --no-audit --no-fund
fi
npm run build
cd "$ROOT"

exec ./.venv/Scripts/python.exe -m uvicorn app.main:app \
  --app-dir apps/sut/backend \
  --port 8000 \
  --reload
