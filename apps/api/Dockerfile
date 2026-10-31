# ==============================================================================
# VN STOCK PREDICTION PLATFORM — BACKEND API DOCKERFILE
# ==============================================================================
# Python 3.11-slim production container with monorepo dependency support,
# automated Alembic migrations, and Uvicorn ASGI server.
# ==============================================================================

FROM python:3.11-slim

WORKDIR /app

# Set environment variables for Python runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/apps/api:/app/apps/ml"

# Install system dependencies (compiler for C-extensions, libpq, and curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast, reliable package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy apps/ml module into monorepo context
COPY apps/ml /app/apps/ml

# Copy apps/api module into monorepo context
COPY apps/api /app/apps/api

# Set working directory to apps/api where alembic.ini, pyproject.toml and app/ reside
WORKDIR /app/apps/api

# Install ML package and API package dependencies into system python
RUN uv pip install --system --no-cache -e /app/apps/ml && \
    uv pip install --system --no-cache -e /app/apps/api

EXPOSE 8000

# Automated migration execution followed by server startup
CMD ["/bin/sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
