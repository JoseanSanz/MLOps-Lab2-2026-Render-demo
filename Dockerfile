# ---------------------------------------------------------------------------
# Stage 1 (builder): installs the runtime dependencies from uv.lock
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# Compile .pyc files at install time (faster start-up) and copy instead of
# hard-linking (the cache and the venv are in different layers)
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv

WORKDIR /app

# Only the dependency files: this layer is cached while they do not change
COPY pyproject.toml uv.lock ./

# --frozen: use exactly the versions of uv.lock (the same ones tested in CI)
# --no-dev: skip the development group (pytest, pylint, black, gradio, ...)
# --no-install-project: install only the dependencies; the code is copied later
RUN uv sync --frozen --no-dev --no-install-project

# ---------------------------------------------------------------------------
# Stage 2 (runtime): only the virtual environment and the source code
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000

WORKDIR /app

# Non-root user to run the application
RUN useradd --create-home --uid 1000 appuser

COPY --from=builder /app/.venv /app/.venv
COPY api ./api
COPY mylib ./mylib
COPY templates ./templates

USER appuser

EXPOSE 8000

# Docker marks the container as unhealthy if /health does not answer
# (python is used because the slim image does not include curl)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:%s/health' % os.environ.get('PORT', '8000'), timeout=4)" || exit 1

# Render provides the port in the PORT environment variable (8000 by default here)
CMD ["sh", "-c", "exec uvicorn api.api:app --host 0.0.0.0 --port ${PORT}"]
