"""Automated Validation Tests for Milestone 4: DevOps, Docker & 1-Click Deployment.

Verifies:
1. Docker Compose specification syntax, services, network, volume, and healthchecks.
2. apps/api/Dockerfile: Python 3.11-slim, monorepo context, uv pip install, alembic migrations startup.
3. apps/web/Dockerfile: Multi-stage standalone build, non-root runner, Next.js static asset mapping.
4. .env.example: Production-ready environment variables and Vietnam market microstructure defaults.
5. .dockerignore hygiene and security: Zero hardcoded seed credentials.
"""

import os
import shutil
import subprocess
from pathlib import Path
import yaml
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INFRA_DIR = REPO_ROOT / "infra"
COMPOSE_FILE = INFRA_DIR / "docker-compose.yml"
API_DOCKERFILE = REPO_ROOT / "apps" / "api" / "Dockerfile"
WEB_DOCKERFILE = REPO_ROOT / "apps" / "web" / "Dockerfile"
ROOT_ENV_EXAMPLE = REPO_ROOT / ".env.example"
INFRA_ENV_EXAMPLE = INFRA_DIR / ".env.example"
API_DOCKERIGNORE = REPO_ROOT / "apps" / "api" / ".dockerignore"
WEB_DOCKERIGNORE = REPO_ROOT / "apps" / "web" / ".dockerignore"
ROOT_DOCKERIGNORE = REPO_ROOT / ".dockerignore"


@pytest.fixture(scope="session")
def compose_data():
    """Load and parse docker-compose.yml."""
    assert COMPOSE_FILE.exists(), f"Compose file not found at {COMPOSE_FILE}"
    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def test_docker_compose_cli_validation():
    """Verify that docker compose config parses cleanly via docker CLI if available."""
    docker_bin = shutil.which("docker")
    if docker_bin:
        cmd = [docker_bin, "compose", "-f", str(COMPOSE_FILE), "config"]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert proc.returncode == 0, f"docker compose config failed:\n{proc.stderr}"
    else:
        pytest.skip("Docker CLI not installed on host machine.")


def test_docker_compose_services_definition(compose_data):
    """Verify all 3 mandatory services exist with correct configuration."""
    services = compose_data.get("services", {})
    assert "vn_stock_db" in services, "Service vn_stock_db missing from compose"
    assert "vn_stock_api" in services, "Service vn_stock_api missing from compose"
    assert "vn_stock_web" in services, "Service vn_stock_web missing from compose"


def test_vn_stock_db_service_config(compose_data):
    """Verify vn_stock_db configuration (PostgreSQL 16 Alpine, volumes, healthcheck)."""
    db = compose_data["services"]["vn_stock_db"]
    assert db.get("image") == "postgres:16-alpine"
    assert db.get("container_name") == "vn_stock_db"
    assert db.get("restart") == "unless-stopped"

    # Environment variables
    env = db.get("environment", {})
    assert "POSTGRES_USER" in env
    assert "POSTGRES_PASSWORD" in env
    assert "POSTGRES_DB" in env
    assert "PGDATA" in env

    # Volumes
    volumes = db.get("volumes", [])
    has_pgdata = any("pgdata:/var/lib/postgresql/data" in str(v) for v in volumes)
    assert has_pgdata, "vn_stock_db must mount pgdata named volume to /var/lib/postgresql/data"

    # Healthcheck
    healthcheck = db.get("healthcheck", {})
    assert healthcheck, "vn_stock_db must declare healthcheck"
    test_cmd = str(healthcheck.get("test", ""))
    assert "pg_isready" in test_cmd, "vn_stock_db healthcheck must use pg_isready"
    assert healthcheck.get("interval") in ["5s", 5]
    assert healthcheck.get("retries") == 5


def test_vn_stock_api_service_config(compose_data):
    """Verify vn_stock_api configuration (build context, env, dependencies, healthcheck, command)."""
    api = compose_data["services"]["vn_stock_api"]
    assert api.get("container_name") == "vn_stock_api"
    assert api.get("restart") == "unless-stopped"

    # Build context
    build = api.get("build", {})
    assert build.get("context") in ["..", str(REPO_ROOT)]
    assert "apps/api/Dockerfile" in build.get("dockerfile")

    # Command: alembic upgrade head && uvicorn
    cmd = str(api.get("command", ""))
    assert "alembic upgrade head" in cmd, "API command must execute alembic upgrade head"
    assert "uvicorn app.main:app" in cmd, "API command must start uvicorn"

    # Inter-service dependency
    depends_on = api.get("depends_on", {})
    assert "vn_stock_db" in depends_on, "vn_stock_api must depend on vn_stock_db"
    assert depends_on["vn_stock_db"].get("condition") == "service_healthy"

    # Environment wiring
    env = api.get("environment", {})
    assert "DATABASE_URL" in env
    assert "vn_stock_db:5432" in str(env["DATABASE_URL"])
    assert "postgresql+asyncpg://" in str(env["DATABASE_URL"])
    assert "SECRET_KEY" in env
    assert "CORS_ORIGINS" in env
    assert "ENVIRONMENT" in env

    # Healthcheck
    healthcheck = api.get("healthcheck", {})
    assert healthcheck, "vn_stock_api must define healthcheck"
    assert "/health" in str(healthcheck.get("test", ""))


def test_vn_stock_web_service_config(compose_data):
    """Verify vn_stock_web configuration (build context, internal and external API URLs, dependencies)."""
    web = compose_data["services"]["vn_stock_web"]
    assert web.get("container_name") == "vn_stock_web"
    assert web.get("restart") == "unless-stopped"

    # Build context
    build = web.get("build", {})
    assert build.get("context") in ["../apps/web", ".."]
    assert "Dockerfile" in build.get("dockerfile")

    # Inter-service dependency
    depends_on = web.get("depends_on", {})
    assert "vn_stock_api" in depends_on, "vn_stock_web must depend on vn_stock_api"

    # Environment variables
    env = web.get("environment", {})
    assert "NEXT_PUBLIC_API_URL" in env
    assert "API_INTERNAL_URL" in env
    assert "vn_stock_api:8000" in str(env["API_INTERNAL_URL"])
    assert env.get("PORT") in [3000, "3000"]
    assert env.get("HOSTNAME") == "0.0.0.0"


def test_docker_compose_networks_and_volumes(compose_data):
    """Verify dedicated bridge network and named persistent volume."""
    volumes = compose_data.get("volumes", {})
    assert "pgdata" in volumes, "Volume pgdata must be declared in root volumes"

    networks = compose_data.get("networks", {})
    assert "vn_stock_net" in networks, "Network vn_stock_net must be declared"

    # All services must belong to vn_stock_net
    for service_name in ["vn_stock_db", "vn_stock_api", "vn_stock_web"]:
        svc_networks = compose_data["services"][service_name].get("networks", [])
        assert "vn_stock_net" in svc_networks, f"Service {service_name} must connect to vn_stock_net"


def test_api_dockerfile_structure():
    """Verify apps/api/Dockerfile complies with Python 3.11-slim and monorepo packaging."""
    assert API_DOCKERFILE.exists()
    content = API_DOCKERFILE.read_text(encoding="utf-8")

    assert "FROM python:3.11-slim" in content, "Must use python:3.11-slim"
    assert "COPY apps/ml /app/apps/ml" in content, "Must copy apps/ml"
    assert "COPY apps/api /app/apps/api" in content, "Must copy apps/api"
    assert "WORKDIR /app/apps/api" in content, "Working directory must be /app/apps/api"
    assert "alembic upgrade head" in content, "Must run alembic upgrade head"
    assert "uvicorn app.main:app" in content, "Must run uvicorn app.main:app"
    assert "EXPOSE 8000" in content, "Must expose port 8000"


def test_web_dockerfile_multistage_standalone():
    """Verify apps/web/Dockerfile uses clean multi-stage standalone build."""
    assert WEB_DOCKERFILE.exists()
    content = WEB_DOCKERFILE.read_text(encoding="utf-8")

    assert "FROM node:20-alpine AS deps" in content or "AS deps" in content
    assert "FROM node:20-alpine AS builder" in content or "AS builder" in content
    assert "FROM node:20-alpine AS runner" in content or "AS runner" in content
    assert "npm run build" in content, "Builder stage must execute npm run build"
    assert ".next/standalone" in content, "Runner must copy .next/standalone"
    assert ".next/static" in content, "Runner must copy .next/static"
    assert "server.js" in content, "Must execute node server.js"
    assert "nextjs" in content, "Must run as non-root user (nextjs)"
    assert "EXPOSE 3000" in content, "Must expose port 3000"


def test_env_example_completeness():
    """Verify .env.example contains all required environment variables and financial parameters."""
    assert ROOT_ENV_EXAMPLE.exists(), ".env.example must exist at repo root"
    assert INFRA_ENV_EXAMPLE.exists(), ".env.example should also exist in infra/"

    content = ROOT_ENV_EXAMPLE.read_text(encoding="utf-8")
    required_keys = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "DATABASE_URL",
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "ALGORITHM",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "REFRESH_TOKEN_EXPIRE_DAYS",
        "CORS_ORIGINS",
        "NEXT_PUBLIC_API_URL",
        "API_INTERNAL_URL",
        "ENVIRONMENT",
    ]
    for key in required_keys:
        assert f"{key}=" in content, f"Missing required env key: {key} in .env.example"

    # Verify Vietnam stock market microstructure documentation in .env.example
    assert "0.15%" in content or "0.0015" in content, "Must document 0.15% fee"
    assert "0.10%" in content or "0.0010" in content, "Must document 0.10% tax"
    assert "T+2.5" in content or "T+3" in content, "Must document T+2.5 settlement cycle"


def test_dockerignore_coverage():
    """Verify dockerignore files exist and exclude node_modules, .next, and virtualenvs."""
    assert API_DOCKERIGNORE.exists(), "apps/api/.dockerignore must exist"
    assert WEB_DOCKERIGNORE.exists(), "apps/web/.dockerignore must exist"
    assert ROOT_DOCKERIGNORE.exists(), "Root .dockerignore must exist"

    web_ignore = WEB_DOCKERIGNORE.read_text(encoding="utf-8")
    assert "node_modules" in web_ignore
    assert ".next" in web_ignore

    api_ignore = API_DOCKERIGNORE.read_text(encoding="utf-8")
    assert ".venv" in api_ignore
    assert "__pycache__" in api_ignore


def test_zero_seed_credentials_or_prebaked_users():
    """Verify no hardcoded seed accounts or passwords are inserted in migrations or compose files."""
    migration_dir = REPO_ROOT / "apps" / "api" / "alembic" / "versions"
    for m in migration_dir.glob("*.py"):
        content = m.read_text(encoding="utf-8")
        assert "bulk_insert" not in content, f"Migration {m.name} must not bulk_insert seed data"
        assert "INSERT INTO users" not in content, f"Migration {m.name} must not insert users"
