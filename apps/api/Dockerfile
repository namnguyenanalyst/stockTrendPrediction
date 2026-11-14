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
    UV_HTTP_TIMEOUT=300 \
    PYTHONPATH="/app/apps/api:/app/apps/ml"

# Install system dependencies (compiler for C-extensions, libpq, and curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast, reliable package management
RUN pip install --no-cache-dir uv

# Copy apps/ml module into monorepo context
COPY apps/ml /app/apps/ml

# Copy apps/api module into monorepo context
COPY apps/api /app/apps/api

# Set working directory to apps/api where alembic.ini, pyproject.toml and app/ reside
WORKDIR /app/apps/api

# Respect platform-specific locked sources, including the explicit CPU-only torch index.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/app/apps/api/.venv/bin:$PATH"

EXPOSE 8000

# The inference container only reads mounted data/models. Training needs a separate writer.
RUN useradd --create-home --uid 1001 apiuser
USER apiuser

# Automated migration execution followed by server startup
CMD ["/bin/sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
