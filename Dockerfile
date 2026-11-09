# syntax=docker/dockerfile:1

# --- builder: resolve and install dependencies with uv ---------------------
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# No RUN --mount here: Railway rejects cache mounts unless their id hardcodes
# the service id, which would tie this file to one service.

# Dependency layer: only invalidated when pyproject.toml or uv.lock change.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

# Project layer: install the package itself (non-editable, so the runtime
# image does not need the source tree).
COPY README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

# --- runtime: slim image, non-root, venv only -------------------------------
FROM python:3.13-slim-bookworm AS runtime

RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    APP_MODULE=cabinet.main:app

USER app
EXPOSE 8000

# Shell form so ${PORT} is expanded at runtime (Railway injects it).
# exec replaces the shell so uvicorn is PID 1 and receives SIGTERM.
# No secret is baked in: configuration comes from the runtime environment.
# No access log: each line would hold the visitor's IP (personal data).
CMD exec uvicorn "$APP_MODULE" --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --no-access-log
