FROM node:24-alpine AS frontend

WORKDIR /app/apps/sut/frontend
COPY apps/sut/frontend/package.json apps/sut/frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY apps/sut/frontend/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/sut/backend ./apps/sut/backend
COPY docs/learning ./docs/learning
COPY docs/portfolio ./docs/portfolio
COPY --from=frontend /app/apps/sut/frontend/dist ./apps/sut/frontend/dist

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request,sys; port=os.getenv('PORT','8000'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=3).status==200 else 1)"
CMD ["sh", "-c", "uvicorn app.main:app --app-dir apps/sut/backend --host 0.0.0.0 --port ${PORT:-8000}"]
