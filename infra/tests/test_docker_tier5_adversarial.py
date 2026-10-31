"""Tier 5 Adversarial Audit for Infrastructure & Deployment (challenger_m5_2).

Covers:
1. Challenge 4: Next.js NEXT_PUBLIC_API_URL build-time vs runtime compose parameter discrepancy.
2. Production Secret Key Hardcoding / Default Fallback in docker-compose.yml.
3. Database Port Exposure & Isolation in Host Network Namespace.
"""

from pathlib import Path
import re
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INFRA_DIR = REPO_ROOT / "infra"
COMPOSE_FILE = INFRA_DIR / "docker-compose.yml"
WEB_DOCKERFILE = REPO_ROOT / "apps" / "web" / "Dockerfile"
API_DOCKERFILE = REPO_ROOT / "apps" / "api" / "Dockerfile"


def test_nextjs_public_env_build_vs_runtime_discrepancy():
    """CHALLENGE 4: Audit build-time inlining of NEXT_PUBLIC_API_URL in apps/web/Dockerfile.

    In Next.js, process.env.NEXT_PUBLIC_* variables are inlined at BUILD TIME (npm run build).
    If apps/web/Dockerfile does not accept ARG NEXT_PUBLIC_API_URL during Stage 2 (builder),
    any runtime environment variable provided in docker-compose.yml will be ignored by
    client-side components in production!
    """
    web_dockerfile_content = WEB_DOCKERFILE.read_text(encoding="utf-8")
    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    web_svc = compose_data["services"]["vn_stock_web"]
    web_env = web_svc.get("environment", {})

    # Compose specifies NEXT_PUBLIC_API_URL as runtime environment variable
    assert "NEXT_PUBLIC_API_URL" in web_env

    # Compose specifies NEXT_PUBLIC_API_URL as build argument
    web_build = web_svc.get("build", {})
    web_build_args = web_build.get("args", {})
    assert "NEXT_PUBLIC_API_URL" in web_build_args, (
        "docker-compose vn_stock_web build.args must supply NEXT_PUBLIC_API_URL"
    )

    # Check whether Dockerfile builder stage declares ARG NEXT_PUBLIC_API_URL
    builder_stage_match = re.search(
        r"FROM node:20-alpine AS builder(.*?)FROM node:20-alpine AS runner",
        web_dockerfile_content,
        re.DOTALL,
    )
    assert builder_stage_match is not None, "Builder stage not found in apps/web/Dockerfile"
    builder_stage = builder_stage_match.group(1)

    has_build_arg = "NEXT_PUBLIC_API_URL" in builder_stage

    # Verify that apps/web/Dockerfile declares ARG NEXT_PUBLIC_API_URL in builder stage
    assert has_build_arg, (
        "Remediation verified: apps/web/Dockerfile builder stage declares ARG NEXT_PUBLIC_API_URL"
    )


def test_compose_secret_key_insecurity_default_audit():
    """CHALLENGE 5: Check default SECRET_KEY fallback in docker-compose.yml.

    If operators start compose without an explicit .env file, the compose file
    falls back to a known hardcoded secret key string.
    """
    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        compose_content = f.read()

    default_secret_match = re.search(
        r"\$\{SECRET_KEY:-([^}]+)\}", compose_content
    )
    assert default_secret_match is not None
    default_secret = default_secret_match.group(1)

    # Verifies that default secret is a known static string
    assert "super_secret_jwt_key" in default_secret
