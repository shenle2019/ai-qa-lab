FROM node:24-alpine AS frontend

RUN apk add --no-cache git
WORKDIR /src
RUN git clone --depth 1 https://github.com/shenle2019/ai-qa-lab.git .

WORKDIR /src/apps/sut/frontend
RUN npm ci --no-audit --no-fund
RUN npm run build

FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN git clone --depth 1 https://github.com/shenle2019/ai-qa-lab.git .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=frontend /src/apps/sut/frontend/dist ./apps/sut/frontend/dist

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SEED_DEMO=1 \
    PORT=7860

EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --app-dir apps/sut/backend --host 0.0.0.0 --port ${PORT}"]
