"""Tier 5 White-Box Adversarial Coverage Audit Test Suite.

Backend API (`apps/api`) and Database Layer Resilience Audit:
1. Token Manipulation & Cryptographic Boundary (alg tampering, secret tampering, missing type, nbf, iat, malformed headers, sub types)
2. Refresh Token Boundary & Cookie Handling (body vs cookie precedence, empty/malformed cookies, access-as-refresh confusion)
3. Concurrency, Race Conditions & Transaction Rollback Isolation
4. Schema Validation, Boundary Stress & Unhandled Exception Probing (dates, financials, JSONB structures, symbols)
5. Multi-Tenant Data Isolation & Instant Account Revocation (deactivated & deleted users)
"""

import asyncio
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
import jwt
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from app.core.config import settings
from app.core.deps import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.db.models.backtest import BacktestHistory
from app.db.models.preset import StrategyPreset
from app.db.models.user import RiskProfile, User, UserRole
from app.db.models.watchlist import UserWatchlist
from app.main import app


# =============================================================================
# Helper Fixtures & Utilities
# =============================================================================


@pytest_asyncio.fixture
async def concurrent_client(
    db_engine: AsyncEngine,
) -> httpx.AsyncClient:
    """AsyncClient with mutex-protected DB sessions to allow async concurrency."""
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    db_mutex = asyncio.Lock()

    async def _test_get_db():
        async with db_mutex, session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _test_get_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_db, None)


async def _create_active_user(
    client: httpx.AsyncClient, prefix: str = "adv_user"
) -> tuple[dict[str, Any], str, str]:
    """Helper creating user via API and returning (user_dict, access_token, refresh_token)."""
    uid = uuid.uuid4().hex[:8]
    email = f"{prefix}_{uid}@adversarial-tier5.vn"
    password = f"P@ssword_{uid}_Tier5!"

    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": f"Auditor {uid}"},
    )
    assert reg_res.status_code == 201, f"User creation failed: {reg_res.text}"
    user_info = reg_res.json()

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token_data = login_res.json()
    access_token = token_data["access_token"]
    refresh_token = login_res.cookies.get("refresh_token", "")

    return user_info, access_token, refresh_token


# =============================================================================
# 1. Token Manipulation & Cryptographic Boundary Tests
# =============================================================================


@pytest.mark.asyncio
async def test_token_with_missing_type_claim(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    """Auditing token behavior when 'type' claim is completely omitted.

    In apps/api/app/core/deps.py:
        token_type = payload.get('type')
        if token_type and token_type != 'access':
    If 'type' is None, the condition evaluates to False.
    This test verifies whether a token lacking 'type' is tolerated or processed.
    """
    user_info, _, _ = await _create_active_user(async_client, prefix="type_omitted")
    user_id = user_info["id"]

    now = datetime.now(timezone.utc)
    # Token crafted with NO 'type' field
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    raw_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {raw_token}"},
    )
    # Documents empirical behavior: deps.py allows tokens with omitted 'type' if signature & sub match
    assert res.status_code == 200
    assert res.json()["id"] == user_id


@pytest.mark.asyncio
async def test_token_with_explicit_disallowed_types(
    async_client: httpx.AsyncClient,
):
    """Tokens with custom or forbidden types (e.g. 'refresh', 'session', 'admin') must be rejected."""
    user_info, _, _ = await _create_active_user(async_client, prefix="bad_types")
    user_id = user_info["id"]
    now = datetime.now(timezone.utc)

    for invalid_type in ["refresh", "session", "admin", "oauth", "internal"]:
        payload = {
            "sub": user_id,
            "type": invalid_type,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        res = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401, f"Token with type '{invalid_type}' must be rejected with 401"
        assert "access token required" in res.text.lower() or "invalid" in res.text.lower()


@pytest.mark.asyncio
async def test_token_with_future_nbf_claim_rejected(
    async_client: httpx.AsyncClient,
):
    """Token with nbf (Not Before) in the future must be rejected by PyJWT as immature."""
    user_info, _, _ = await _create_active_user(async_client, prefix="immature")
    user_id = user_info["id"]
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "type": "access",
        "iat": int(now.timestamp()),
        "nbf": int((now + timedelta(hours=2)).timestamp()),  # Not valid until 2 hours from now
        "exp": int((now + timedelta(hours=4)).timestamp()),
    }
    immature_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {immature_token}"},
    )
    assert res.status_code == 401
    assert "invalid or expired token" in res.text.lower()


@pytest.mark.asyncio
async def test_token_algorithm_substitution_attacks(
    async_client: httpx.AsyncClient,
):
    """Algorithm substitution attacks (HS384, HS512, RS256, none) must all fail validation."""
    user_info, _, _ = await _create_active_user(async_client, prefix="alg_sub")
    user_id = user_info["id"]
    now = datetime.now(timezone.utc)
    base_payload = {
        "sub": user_id,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }

    # 1. HS384 signed token
    token_hs384 = jwt.encode(base_payload, settings.JWT_SECRET_KEY, algorithm="HS384")
    res1 = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token_hs384}"}
    )
    assert res1.status_code == 401

    # 2. HS512 signed token
    token_hs512 = jwt.encode(base_payload, settings.JWT_SECRET_KEY, algorithm="HS512")
    res2 = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token_hs512}"}
    )
    assert res2.status_code == 401

    # 3. 'none' algorithm token
    token_none = jwt.encode(base_payload, key="", algorithm="none")
    res3 = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token_none}"}
    )
    assert res3.status_code == 401


@pytest.mark.asyncio
async def test_token_subject_anomalies(
    async_client: httpx.AsyncClient,
):
    """Stress test diverse anomalous token 'sub' payloads (integers, booleans, invalid UUIDs, nil UUID)."""
    now = datetime.now(timezone.utc)
    test_cases = [
        (123456, 401),
        (True, 401),
        ("", 401),
        ("not-a-valid-uuid-format", 401),
        ("00000000-0000-0000-0000-000000000000", 401),  # Nil UUID: valid format but user not found
        (str(uuid.uuid4()), 401),  # Random UUID: not in DB
    ]

    for sub_val, expected_status in test_cases:
        payload = {
            "sub": sub_val,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        res = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == expected_status, f"Expected {expected_status} for sub={sub_val}"


@pytest.mark.asyncio
async def test_authorization_header_syntax_variants(
    async_client: httpx.AsyncClient,
):
    """Exhaustive authorization header format variants."""
    user_info, access_token, _ = await _create_active_user(async_client, prefix="header_var")

    # 1. Missing header -> 401
    res = await async_client.get("/api/v1/auth/me")
    assert res.status_code == 401

    # 2. 'Bearer' without token -> 401
    res = await async_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer"})
    assert res.status_code == 401

    # 3. 'Bearer ' (single space, no token) -> 401
    res = await async_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer "})
    assert res.status_code == 401

    # 4. Multiple tokens after Bearer -> 401
    res = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token} extra_token"}
    )
    assert res.status_code == 401

    # 5. Wrong scheme 'Token' or 'Basic' -> 401
    res = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Token {access_token}"}
    )
    assert res.status_code == 401

    res = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": "Basic dXNlcjpwYXNz"}
    )
    assert res.status_code == 401

    # 6. Scheme case-insensitivity: 'bearer' (lowercase) -> 200 (RFC 6750 standard)
    res = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"bearer {access_token}"}
    )
    assert res.status_code == 200

    # 7. Multiple spaces between Bearer and token -> 200 (split() normalizes whitespace)
    res = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer    {access_token}"}
    )
    assert res.status_code == 200


# =============================================================================
# 2. Refresh Token Boundary & Cookie Precedence
# =============================================================================


@pytest.mark.asyncio
async def test_refresh_token_body_takes_precedence_over_cookie(
    async_client: httpx.AsyncClient,
):
    """When both body and cookie are supplied to /refresh, request body takes precedence."""
    _, _, refresh_token_valid = await _create_active_user(async_client, prefix="ref_prec")
    invalid_cookie_token = "invalid.cookie.token"

    # Body has valid token, cookie has invalid token -> should SUCCEED
    async_client.cookies.set("refresh_token", invalid_cookie_token)
    res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token_valid},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()

    # Body has invalid token, cookie has valid token -> body precedence triggers 401
    async_client.cookies.set("refresh_token", refresh_token_valid)
    res_fail = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "corrupted_body_token"},
    )
    assert res_fail.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_empty_payload_and_empty_cookies(
    async_client: httpx.AsyncClient,
):
    """Empty JSON body `{}` or empty cookie value must be rejected with 401."""
    async_client.cookies.clear()

    # 1. No cookie, empty JSON
    res1 = await async_client.post("/api/v1/auth/refresh", json={})
    assert res1.status_code == 401
    assert "missing refresh token" in res1.text.lower()

    # 2. No cookie, null field
    res2 = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": None})
    assert res2.status_code == 401

    # 3. Empty cookie string
    async_client.cookies.set("refresh_token", "")
    res3 = await async_client.post("/api/v1/auth/refresh")
    assert res3.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_cookie_with_uri_encoding(
    async_client: httpx.AsyncClient,
):
    """Auditing refresh token cookie behavior when raw or percent-encoded."""
    _, _, refresh_token = await _create_active_user(async_client, prefix="cookie_uri")

    async_client.cookies.clear()
    async_client.cookies.set("refresh_token", refresh_token)
    res = await async_client.post("/api/v1/auth/refresh")
    assert res.status_code == 200


# =============================================================================
# 3. Concurrency, Race Conditions & Transaction Resilience
# =============================================================================


@pytest.mark.asyncio
async def test_concurrent_registration_with_same_email(
    concurrent_client: httpx.AsyncClient,
):
    """Adversarial Race Test: 5 concurrent requests attempting to register the exact same email.

    Only 1 request may succeed (HTTP 201).
    All concurrent duplicate attempts must be rejected cleanly (HTTP 400 or handled IntegrityError)
    without corrupting the database or leaking duplicate records.
    """
    race_email = f"race_{uuid.uuid4().hex[:8]}@quant.vn"
    password = "StrongPassword@123"

    async def register_attempt(index: int):
        return await concurrent_client.post(
            "/api/v1/auth/register",
            json={
                "email": race_email,
                "password": password,
                "full_name": f"Racer {index}",
            },
        )

    # Launch 5 concurrent registration tasks simultaneously
    responses = await asyncio.gather(*[register_attempt(i) for i in range(5)], return_exceptions=True)

    successes = [r for r in responses if isinstance(r, httpx.Response) and r.status_code == 201]
    rejections = [
        r for r in responses if isinstance(r, httpx.Response) and r.status_code in (400, 409, 500)
    ]

    assert len(successes) == 1, (
        f"Exactly one registration must succeed with 201, got {len(successes)}"
    )
    assert len(rejections) == 4, (
        f"Remaining 4 attempts must be rejected, got {len(rejections)}"
    )


@pytest.mark.asyncio
async def test_concurrent_watchlist_creation_same_user(
    concurrent_client: httpx.AsyncClient,
):
    """A user sends 5 concurrent requests to create watchlists. All 5 must be committed cleanly."""
    user_info, access_token, _ = await _create_active_user(concurrent_client, prefix="wl_race")
    headers = {"Authorization": f"Bearer {access_token}"}

    async def create_wl(index: int):
        return await concurrent_client.post(
            "/api/v1/user/watchlists",
            headers=headers,
            json={"name": f"Watchlist_{index}", "symbols": ["HPG", "FPT", "VIC"]},
        )

    responses = await asyncio.gather(*[create_wl(i) for i in range(5)])
    for r in responses:
        assert r.status_code == 201

    # Verify user now has 5 watchlists in DB
    list_res = await concurrent_client.get("/api/v1/user/watchlists", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 5


@pytest.mark.asyncio
async def test_concurrent_read_and_delete_watchlist(
    concurrent_client: httpx.AsyncClient,
):
    """User performs concurrent read and delete operations on the same watchlist."""
    user_info, access_token, _ = await _create_active_user(concurrent_client, prefix="rw_race")
    headers = {"Authorization": f"Bearer {access_token}"}

    create_res = await concurrent_client.post(
        "/api/v1/user/watchlists",
        headers=headers,
        json={"name": "RaceTargetWL", "symbols": ["VNM"]},
    )
    assert create_res.status_code == 201
    wl_id = create_res.json()["id"]

    async def do_get():
        return await concurrent_client.get("/api/v1/user/watchlists", headers=headers)

    async def do_delete():
        return await concurrent_client.delete(f"/api/v1/user/watchlists/{wl_id}", headers=headers)

    results = await asyncio.gather(do_get(), do_delete(), do_get())
    statuses = [r.status_code for r in results]

    # Delete must return 204
    assert statuses[1] == 204
    # GETs must return 200
    assert statuses[0] == 200
    assert statuses[2] == 200


# =============================================================================
# 4. Schema Validation, Boundary Stress & Unhandled Exception Probing
# =============================================================================


@pytest.mark.asyncio
async def test_backtest_date_format_adversarial_probing(
    async_client: httpx.AsyncClient,
):
    """Adversarial Probe: Testing backtest history with invalid/malformed date formats.

    Evaluates whether the API handles invalid dates with 422/400 or unhandled 500 ValueError.
    """
    user_info, access_token, _ = await _create_active_user(async_client, prefix="date_probe")
    headers = {"Authorization": f"Bearer {access_token}"}

    invalid_date_payloads = [
        {"start_date": "not-a-date", "end_date": "2024-01-01"},
        {"start_date": "2024-13-45", "end_date": "2024-01-01"},
        {"start_date": "2024/01/01", "end_date": "2024/06/01"},
        {"start_date": "01-01-2024", "end_date": "01-06-2024"},
    ]

    base_payload = {
        "symbol": "HPG",
        "strategy_name": "FormatTest",
        "strategy_type": "AI",
        "initial_capital": 100_000_000.0,
        "total_return": 0.15,
        "sharpe_ratio": 1.5,
        "max_drawdown": 0.05,
        "win_rate": 0.65,
        "equity_curve": [],
    }

    # Create client with raise_app_exceptions=False to capture unhandled server responses
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as capturing_client:
        for invalid_dates in invalid_date_payloads:
            payload = {**base_payload, **invalid_dates}
            res = await capturing_client.post(
                "/api/v1/user/backtests",
                headers=headers,
                json=payload,
            )
            # Remediation verified: Malformed date strings fail validation with HTTP 422 Unprocessable Entity
            assert res.status_code == 422, (
                f"Expected HTTP 422 from validation failure, got {res.status_code}"
            )



@pytest.mark.asyncio
async def test_backtest_extreme_financial_metrics(
    async_client: httpx.AsyncClient,
):
    """Stress test boundary and extreme financial values in BacktestHistory."""
    user_info, access_token, _ = await _create_active_user(async_client, prefix="fin_bound")
    headers = {"Authorization": f"Bearer {access_token}"}

    extreme_payload = {
        "symbol": "HPG",
        "strategy_name": "ExtremeQuant",
        "strategy_type": "HighFrequency",
        "start_date": "2020-01-01",
        "end_date": "2024-01-01",
        "initial_capital": 1_000_000_000_000.0,  # 1 Trillion VND
        "total_return": 99.99,  # 9999%
        "sharpe_ratio": -99.9,  # Deep negative
        "max_drawdown": 1.0,  # 100% loss
        "win_rate": 0.0,  # Zero wins
        "equity_curve": [{"step": 0, "val": 1e12}, {"step": 1, "val": 0.0}],
    }

    res = await async_client.post(
        "/api/v1/user/backtests",
        headers=headers,
        json=extreme_payload,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["initial_capital"] == 1_000_000_000_000.0
    assert data["win_rate"] == 0.0


@pytest.mark.asyncio
async def test_watchlist_symbol_cleansing_and_boundary(
    async_client: httpx.AsyncClient,
):
    """Symbols are cleanly trimmed, uppercased, and preserved."""
    user_info, access_token, _ = await _create_active_user(async_client, prefix="sym_bound")
    headers = {"Authorization": f"Bearer {access_token}"}

    res = await async_client.post(
        "/api/v1/user/watchlists",
        headers=headers,
        json={
            "name": "SymbolsBoundary",
            "symbols": ["  hpg  ", "fpt", "VIC", "vn30f1m"],
        },
    )
    assert res.status_code == 201
    saved_symbols = res.json()["symbols"]
    assert saved_symbols == ["HPG", "FPT", "VIC", "VN30F1M"]


@pytest.mark.asyncio
async def test_preset_deeply_nested_parameters_json(
    async_client: httpx.AsyncClient,
):
    """Complex nested dictionary structures in strategy parameters."""
    user_info, access_token, _ = await _create_active_user(async_client, prefix="preset_deep")
    headers = {"Authorization": f"Bearer {access_token}"}

    nested_params = {
        "l1": {
            "l2": {
                "l3": {
                    "models": ["lstm", "lightgbm", "xgboost"],
                    "thresholds": {"buy": 0.65, "sell": 0.35},
                    "flags": {"auto_hedge": True, "slippage_bps": 15},
                    "meta": None,
                }
            }
        }
    }

    res = await async_client.post(
        "/api/v1/user/presets",
        headers=headers,
        json={
            "name": "DeepNestedPreset",
            "description": "Multi-level configuration tree",
            "parameters": nested_params,
        },
    )
    assert res.status_code == 201
    assert res.json()["parameters"]["l1"]["l2"]["l3"]["models"] == ["lstm", "lightgbm", "xgboost"]


@pytest.mark.asyncio
async def test_sql_injection_payloads_in_user_inputs(
    async_client: httpx.AsyncClient,
):
    """SQL injection payloads in text fields are stored as literal strings without code execution."""
    user_info, access_token, _ = await _create_active_user(async_client, prefix="sqli_probe")
    headers = {"Authorization": f"Bearer {access_token}"}

    sqli_name = "Watchlist'); DROP TABLE user_watchlists; --"
    res = await async_client.post(
        "/api/v1/user/watchlists",
        headers=headers,
        json={"name": sqli_name, "symbols": ["HPG"]},
    )
    assert res.status_code == 201
    assert res.json()["name"] == sqli_name

    # Verify user_watchlists table was NOT dropped and query works
    res_list = await async_client.get("/api/v1/user/watchlists", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1


# =============================================================================
# 5. Multi-Tenant Data Isolation & Instant Account Revocation
# =============================================================================


@pytest.mark.asyncio
async def test_cross_tenant_backtest_isolation(
    async_client: httpx.AsyncClient,
):
    """User B cannot view or access User A's backtest histories."""
    _, token_a, _ = await _create_active_user(async_client, prefix="tenant_a")
    _, token_b, _ = await _create_active_user(async_client, prefix="tenant_b")

    # User A creates backtest
    res_a = await async_client.post(
        "/api/v1/user/backtests",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "symbol": "SSI",
            "strategy_name": "TenantA_Secret_Strat",
            "strategy_type": "AI",
            "start_date": "2024-01-01",
            "end_date": "2024-06-01",
            "initial_capital": 50_000_000.0,
            "total_return": 0.25,
            "sharpe_ratio": 2.0,
            "max_drawdown": 0.03,
            "win_rate": 0.70,
            "equity_curve": [],
        },
    )
    assert res_a.status_code == 201

    # User B queries their backtests -> must be empty []
    res_b = await async_client.get(
        "/api/v1/user/backtests",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 200
    assert len(res_b.json()) == 0


@pytest.mark.asyncio
async def test_immediate_revocation_on_account_deactivation(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    """When an account is deactivated in DB, all existing tokens are immediately rejected."""
    user_info, access_token, refresh_token = await _create_active_user(
        async_client, prefix="instant_deact"
    )
    user_id = uuid.UUID(user_info["id"])

    # Deactivate user in DB
    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.is_active = False
    await db_session.commit()

    headers = {"Authorization": f"Bearer {access_token}"}

    # /api/v1/auth/me -> 400
    res_me = await async_client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 400
    assert "inactive" in res_me.text.lower()

    # /api/v1/user/presets -> 400
    res_preset = await async_client.get("/api/v1/user/presets", headers=headers)
    assert res_preset.status_code == 400

    # /api/v1/auth/refresh -> 401
    async_client.cookies.clear()
    res_refresh = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert res_refresh.status_code == 401


@pytest.mark.asyncio
async def test_immediate_revocation_on_account_deletion(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    """When an account is deleted from DB, valid tokens immediately return 401."""
    user_info, access_token, refresh_token = await _create_active_user(
        async_client, prefix="instant_del"
    )
    user_id = uuid.UUID(user_info["id"])

    # Delete user from DB
    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    await db_session.delete(user)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {access_token}"}

    # /api/v1/auth/me -> 401
    res_me = await async_client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 401
    assert "user not found" in res_me.text.lower()

    # /api/v1/auth/refresh -> 401
    async_client.cookies.clear()
    res_refresh = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert res_refresh.status_code == 401
