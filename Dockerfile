syntax=docker/dockerfile:1.7

############################
# Stage 1: build Frontend  #
############################
FROM node:20-alpine AS frontend-builder
WORKDIR /fe
COPY Frontend/package.json Frontend/pnpm-lock.yaml* ./
RUN corepack enable && corepack prepare pnpm@latest --activate \
 && (pnpm install --frozen-lockfile 2>/dev/null || pnpm install)
COPY Frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

###################################
# Stage 2: install Python deps    #
###################################
FROM python:3.11-slim AS python-deps
WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt        /tmp/api-req.txt
COPY ingestion/requirements.txt  /tmp/ingestion-req.txt
COPY sink/requirements.txt       /tmp/sink-req.txt

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir \
        -r /tmp/api-req.txt \
        -r /tmp/ingestion-req.txt \
        -r /tmp/sink-req.txt

############################
# Stage 3: final image     #
############################
FROM python:3.11-slim AS runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates nodejs \
 && rm -rf /var/lib/apt/lists/*

COPY --from=python-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

WORKDIR /app

COPY api        /app/api
COPY ingestion  /app/ingestion
COPY sink       /app/sink
COPY ml         /app/ml
COPY streaming  /app/streaming
COPY scripts    /app/scripts
COPY storage    /app/storage
COPY pyproject.toml /app/pyproject.toml

COPY --from=frontend-builder /fe/public                /app/frontend/public
COPY --from=frontend-builder /fe/.next/standalone      /app/frontend
COPY --from=frontend-builder /fe/.next/static          /app/frontend/.next/static

COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=8000

EXPOSE 8000 3000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["api"]
