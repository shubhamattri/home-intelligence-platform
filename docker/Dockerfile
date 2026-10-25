# Generic service image. Built once per service via build args in compose.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Workspace metadata + all members (needed for uv to resolve the workspace).
COPY pyproject.toml uv.lock ./
COPY libs ./libs
COPY services ./services
COPY mcp-gateway ./mcp-gateway

ARG PKG
RUN uv sync --frozen --package "${PKG}" --no-dev

# Non-root runtime user. HOME + UV_CACHE_DIR must be writable by this user so
# `uv run` can initialise its cache at runtime.
RUN groupadd --system app && useradd --system --gid app app && chown -R app:app /app
ENV HOME=/app UV_CACHE_DIR=/app/.cache/uv
USER app

ARG APP_MODULE
ARG PORT=8000
ENV APP_MODULE=${APP_MODULE} PORT=${PORT}
EXPOSE ${PORT}
# uvicorn from the synced venv
CMD ["sh", "-c", "uv run --no-sync uvicorn ${APP_MODULE} --host 0.0.0.0 --port ${PORT}"]
