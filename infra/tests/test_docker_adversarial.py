"""Adversarial stress tests for Docker Compose, Dockerfiles, and environment configuration.

Milestone 4 Empirical Challenger Verification Suite:
- Stress-tests environment variable coverage and naming discrepancies.
- Stress-tests special character passwords in DATABASE_URL.
- Stress-tests CORS_ORIGINS override resilience.
- Simulates Alembic startup failure and verifies migration race condition protection.
- Verifies Next.js standalone build structure and non-root runner security.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
import pytest
import yaml
from sqlalchemy.engine import make_url

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INFRA_DIR = REPO_ROOT / "infra"
COMPOSE_FILE = INFRA_DIR / "docker-compose.yml"
ROOT_ENV_EXAMPLE = REPO_ROOT / ".env.example"
INFRA_ENV_EXAMPLE = INFRA_DIR / ".env.example"
API_DOCKERFILE = REPO_ROOT / "apps" / "api" / "Dockerfile"
WEB_DOCKERFILE = REPO_ROOT / "apps" / "web" / "Dockerfile"


@pytest.fixture(scope="module")
def compose_yaml():
    """Load raw yaml content of infra/docker-compose.yml."""
    assert COMPOSE_FILE.exists()
    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_compose_parses_with_zero_env_vars():
    """Verify compose file parses cleanly with zero environment variables set (all defaults)."""
    clean_env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
    }
    docker_bin = shutil.which("docker")
    if not docker_bin:
        pytest.skip("Docker CLI not available")

    cmd = [docker_bin, "compose", "-f", str(COMPOSE_FILE), "config"]
    res = subprocess.run(cmd, env=clean_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, f"docker compose config failed with empty env:\n{res.stderr}"

    config_data = yaml.safe_load(res.stdout)
    api_svc = config_data["services"]["vn_stock_api"]
    assert "postgresql+asyncpg://postgres:postgres@vn_stock_db:5432/vn_stock" == api_svc["environment"]["DATABASE_URL"]
    assert "8000" in str(api_svc["ports"][0]["published"])


def test_cors_origins_hardcoding_issue(compose_yaml):
    """CHALLENGE 1: Check whether CORS_ORIGINS in docker-compose.yml can be overridden via environment.

    Verifies that docker-compose.yml uses ${CORS_ORIGINS:-...} so that production
    deployments with custom domains can override CORS via environment variables.
    """
    api_env = compose_yaml["services"]["vn_stock_api"]["environment"]
    cors_val = api_env.get("CORS_ORIGINS", "")
    is_interpolated = "${CORS_ORIGINS" in str(cors_val)
    # Confirm CORS_ORIGINS is properly interpolated
    assert is_interpolated, "CORS_ORIGINS should be interpolated to support override"


def test_env_example_vs_compose_variable_alignment():
    """CHALLENGE 2: Check for port and variable naming discrepancies between .env.example and compose.

    Verifies that API_PORT and WEB_PORT referenced in docker-compose.yml
    are properly documented in .env.example.
    """
    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        compose_text = f.read()

    compose_vars = set(re.findall(r"\$\{([A-Za-z0-9_]+)(?::-.*?)?\}", compose_text))

    env_example_text = ROOT_ENV_EXAMPLE.read_text(encoding="utf-8")
    env_vars = set(re.findall(r"^([A-Za-z0-9_]+)=", env_example_text, re.MULTILINE))

    # API_PORT and WEB_PORT are documented in .env.example
    assert "API_PORT" in env_vars, "API_PORT must be documented in .env.example"
    assert "WEB_PORT" in env_vars, "WEB_PORT must be documented in .env.example"
    missing_in_env_example = compose_vars - env_vars
    assert len(missing_in_env_example) == 0, f"Unmapped compose variables: {missing_in_env_example}"


def test_special_characters_in_db_password_break_raw_url():
    """CHALLENGE 3: Test whether unencoded special characters in POSTGRES_PASSWORD break DATABASE_URL.

    If a user sets POSTGRES_PASSWORD='p@ss:word#1' in .env, raw string substitution in
    docker-compose.yml produces an invalid URL that SQLAlchemy/asyncpg fails to parse.
    """
    raw_password = "p@ss:word#1"
    raw_url = f"postgresql+asyncpg://postgres:{raw_password}@vn_stock_db:5432/vn_stock"

    # Verifies that raw unencoded password causes make_url to crash or parse incorrectly
    with pytest.raises(ValueError) as excinfo:
        make_url(raw_url)
    assert "invalid literal for int()" in str(excinfo.value)


def test_api_internal_url_unused_in_frontend():
    """CHALLENGE 4: Verify whether API_INTERNAL_URL is actually used anywhere in apps/web.

    Vulnerability: The compose file and .env.example advertise API_INTERNAL_URL for SSR,
    but apps/web/src/lib/api.ts only looks at NEXT_PUBLIC_API_URL.
    """
    web_dir = REPO_ROOT / "apps" / "web"
    found = False
    for p in web_dir.glob("**/*.[tj]s*"):
        if "node_modules" in p.parts or ".next" in p.parts:
            continue
        text = p.read_text(encoding="utf-8")
        if "API_INTERNAL_URL" in text:
            found = True
            break
    assert not found, "API_INTERNAL_URL is unexpectedly used in apps/web"


def test_migration_race_condition_protection(compose_yaml):
    """Verify that vn_stock_api depends on vn_stock_db with condition: service_healthy."""
    api = compose_yaml["services"]["vn_stock_api"]
    depends_on = api.get("depends_on", {})
    assert "vn_stock_db" in depends_on
    assert depends_on["vn_stock_db"].get("condition") == "service_healthy"

    # Verify db has an actual healthcheck command
    db = compose_yaml["services"]["vn_stock_db"]
    assert "healthcheck" in db
    assert "pg_isready" in str(db["healthcheck"]["test"])


def test_web_depends_on_api_healthy(compose_yaml):
    """Verify that vn_stock_web depends on vn_stock_api with condition: service_healthy."""
    web = compose_yaml["services"]["vn_stock_web"]
    depends_on = web.get("depends_on", {})
    assert "vn_stock_api" in depends_on
    assert depends_on["vn_stock_api"].get("condition") == "service_healthy"

    api = compose_yaml["services"]["vn_stock_api"]
    assert "healthcheck" in api
    assert "/health" in str(api["healthcheck"]["test"])


def test_alembic_failure_prevents_uvicorn_launch():
    """Verify that in the API startup command, failure of alembic upgrade head prevents uvicorn launch."""
    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # The command uses '&&' which ensures fail-fast semantics
    assert 'alembic upgrade head && uvicorn' in content

    # Empirically test shell && semantics: if first command fails, second does not run
    cmd = "/bin/sh -c 'exit 1 && echo SHOULD_NOT_PRINT'"
    res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)
    assert res.returncode == 1
    assert "SHOULD_NOT_PRINT" not in res.stdout


def test_dockerfile_monorepo_copy_ordering():
    """Verify apps/api/Dockerfile copies apps/ml and apps/api before running pip install."""
    content = API_DOCKERFILE.read_text(encoding="utf-8")
    ml_copy_pos = content.find("COPY apps/ml")
    api_copy_pos = content.find("COPY apps/api")
    pip_install_pos = content.find("uv pip install")

    assert ml_copy_pos != -1, "Missing COPY apps/ml"
    assert api_copy_pos != -1, "Missing COPY apps/api"
    assert pip_install_pos != -1, "Missing uv pip install"
    assert ml_copy_pos < pip_install_pos, "COPY apps/ml must precede pip install"
    assert api_copy_pos < pip_install_pos, "COPY apps/api must precede pip install"


def test_web_dockerfile_standalone_permissions():
    """Verify apps/web/Dockerfile creates non-root user and assigns chown to .next directory."""
    content = WEB_DOCKERFILE.read_text(encoding="utf-8")
    assert "adduser" in content
    assert "nextjs" in content
    assert "USER nextjs" in content
    assert "--chown=nextjs:nodejs" in content
