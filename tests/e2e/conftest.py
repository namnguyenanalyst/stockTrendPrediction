"""PyTest Fixtures and Configuration for Opaque-Box E2E Tests."""

import os
import sys
from pathlib import Path
import uuid
import pytest
import httpx

# Ensure project root is in sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from tests.e2e.client import E2EClient
from tests.e2e.mock_server import STORE, create_reference_app

E2E_BASE_URL = os.environ.get("E2E_BASE_URL", "").rstrip("/")
E2E_FORCE_MOCK = os.environ.get("E2E_FORCE_MOCK", "").lower() in ("1", "true", "yes")


def _is_live_server_available(url: str) -> bool:
    if not url:
        return False
    try:
        with httpx.Client(timeout=2.0) as check_client:
            res = check_client.get(f"{url}/health")
            return res.status_code == 200
    except Exception:
        return False


# Determine default mode at test session start
LIVE_AVAILABLE = False
if not E2E_FORCE_MOCK and E2E_BASE_URL:
    LIVE_AVAILABLE = _is_live_server_available(E2E_BASE_URL)
elif not E2E_FORCE_MOCK and not E2E_BASE_URL:
    # Try local default port 8000
    if _is_live_server_available("http://localhost:8000"):
        E2E_BASE_URL = "http://localhost:8000"
        LIVE_AVAILABLE = True


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    """Ensure in-memory mock store is fresh for each test if running in reference mode."""
    if not LIVE_AVAILABLE:
        STORE.clear()
    yield
    if not LIVE_AVAILABLE:
        STORE.clear()


@pytest.fixture
def test_app():
    """Reference ASGI application for in-process test runs."""
    if LIVE_AVAILABLE:
        return None
    return create_reference_app()


@pytest.fixture
def client(test_app) -> E2EClient:
    """Create a clean E2EClient targeting live server or in-process ASGI app."""
    if LIVE_AVAILABLE:
        cli = E2EClient(base_url=E2E_BASE_URL)
    else:
        cli = E2EClient(base_url="http://testserver", app=test_app)
    try:
        yield cli
    finally:
        cli.close()


@pytest.fixture
def registered_user(client: E2EClient) -> dict:
    """Register a new user and log them in, returning credentials and user data."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"investor_{unique_id}@quantplatform.vn"
    password = "StrongPassword@123"
    full_name = f"Investor {unique_id}"
    risk_profile = "balanced"

    reg_res = client.register(
        email=email,
        password=password,
        full_name=full_name,
        risk_profile=risk_profile,
    )
    assert reg_res.status_code in (200, 201), f"User registration failed: {reg_res.text}"

    login_res = client.login(email=email, password=password)
    assert login_res.status_code == 200, f"User login failed: {login_res.text}"
    login_data = login_res.json()

    return {
        "email": email,
        "password": password,
        "full_name": full_name,
        "risk_profile": risk_profile,
        "access_token": login_data.get("access_token"),
        "user": login_data.get("user"),
    }


@pytest.fixture
def user_a_client(test_app) -> E2EClient:
    """E2EClient logged in as User A for multi-tenant isolation testing."""
    if LIVE_AVAILABLE:
        cli = E2EClient(base_url=E2E_BASE_URL)
    else:
        cli = E2EClient(base_url="http://testserver", app=test_app)

    unique_id = uuid.uuid4().hex[:8]
    email = f"user_a_{unique_id}@firm.vn"
    pwd = "UserAPassword@123"

    reg = cli.register(email=email, password=pwd, full_name="User Alpha", risk_profile="conservative")
    assert reg.status_code in (200, 201)
    login = cli.login(email=email, password=pwd)
    assert login.status_code == 200

    yield cli
    cli.close()


@pytest.fixture
def user_b_client(test_app) -> E2EClient:
    """E2EClient logged in as User B for multi-tenant isolation testing."""
    if LIVE_AVAILABLE:
        cli = E2EClient(base_url=E2E_BASE_URL)
    else:
        cli = E2EClient(base_url="http://testserver", app=test_app)

    unique_id = uuid.uuid4().hex[:8]
    email = f"user_b_{unique_id}@firm.vn"
    pwd = "UserBPassword@456"

    reg = cli.register(email=email, password=pwd, full_name="User Beta", risk_profile="aggressive")
    assert reg.status_code in (200, 201)
    login = cli.login(email=email, password=pwd)
    assert login.status_code == 200

    yield cli
    cli.close()
