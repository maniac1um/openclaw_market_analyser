FROM node:22-alpine AS frontend-build
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md ./
COPY app ./app
COPY scripts ./scripts
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir .
COPY --from=frontend-build /build/dist ./frontend/dist
RUN mkdir -p content/reports/raw content/reports/rendered \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser
ENV OPENCLAW_SERVE_SPA=true
ENV OPENCLAW_BIND_HOST=0.0.0.0
ENV OPENCLAW_BIND_PORT=8000
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
