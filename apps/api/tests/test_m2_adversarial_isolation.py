"""Adversarial Challenge Test Suite for Milestone 2: Personalization & Multi-Tenant Isolation.

Empirical verification covering:
1. IDOR Attacks (Cross-Tenant Access & Destruction Prevention):
   - User B attempting to view User A's watchlists, presets, and backtests
   - User B attempting to delete User A's watchlist (must return 404)
   - User B attempting to delete User A's preset (must return 404)
   - User B attempting direct GET on User A's watchlist ID or preset ID
   - Privilege injection attempt: passing explicit user_id in payload to hijack ownership
2. Tampered & Malicious UUIDs:
   - Nil UUID (00000000-0000-0000-0000-000000000000)
   - Non-existent random UUID
   - SQL injection strings (' OR 1=1 --, UNION SELECT ...)
   - Path traversal (../../etc/passwd, %00%2e%2e%2f)
   - Malformed, truncated, and oversized strings
3. High-Concurrency Multi-User Portfolio Transactions (10 Virtual Users):
   - 10 virtual users simultaneously registering, logging in, creating, querying, and deleting
   - Zero crosstalk / cross-contamination verification
   - Race-condition cross-tenant delete attempts under concurrent load
4. Auth Security Edge Cases:
   - Token type confusion: Refresh token presented to protected user endpoint
   - Tampered signature JWT access token
   - Inactive user account access denial
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from app.core.deps import get_db
from app.core.security import create_refresh_token
from app.db.models.user import User
from app.main import app


@pytest_asyncio.fixture
async def concurrent_async_client(
    db_engine: AsyncEngine,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Cung cấp httpx.AsyncClient hỗ trợ phiên AsyncSession tuần tự hóa giao dịch SQLite nhưng cho phép client đồng thời."""
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    # Serialize DB transactions on SQLite in-memory to prevent driver lock while stress-testing HTTP client concurrency
    db_mutex = asyncio.Lock()

    async def _test_get_db():
        async with db_mutex, session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _test_get_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_db, None)


async def _register_and_login_helper(client: httpx.AsyncClient, prefix: str) -> tuple[dict, str]:
    """Helper đăng ký tài khoản và đăng nhập trả về thông tin user và access token."""
    uid = uuid.uuid4().hex[:8]
    email = f"{prefix}_{uid}@adversarial-test.vn"
    password = f"AdvPassword@{uid}!"

    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": f"Tester {prefix}"},
    )
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    user_data = reg_res.json()

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    return user_data, token


# =============================================================================
# 1. IDOR Attacks & Cross-Tenant Data Isolation
# =============================================================================


@pytest.mark.asyncio
async def test_adversarial_idor_user_b_cannot_access_or_delete_user_a(
    concurrent_async_client: httpx.AsyncClient,
):
    """Stress Test: User B cannot read, delete, or overwrite User A's private resources."""
    # Step 1: Register and login User A & User B
    _user_a, token_a = await _register_and_login_helper(concurrent_async_client, "user_a")
    _user_b, token_b = await _register_and_login_helper(concurrent_async_client, "user_b")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Step 2: User A creates Watchlist, Strategy Preset, and Backtest History
    wl_a_res = await concurrent_async_client.post(
        "/api/v1/user/watchlists",
        json={"name": "Confidential Alpha Watchlist", "symbols": ["VCB", "BID", "CTG"]},
        headers=headers_a,
    )
    assert wl_a_res.status_code == 201
    wl_a = wl_a_res.json()
    wl_a_id = wl_a["id"]

    preset_a_res = await concurrent_async_client.post(
        "/api/v1/user/presets",
        json={
            "name": "Secret Alpha Strategy Preset",
            "description": "Proprietary momentum model",
            "parameters": {"fast": 10, "slow": 30, "threshold": 0.05},
        },
        headers=headers_a,
    )
    assert preset_a_res.status_code == 201
    preset_a = preset_a_res.json()
    preset_a_id = preset_a["id"]

    bt_a_res = await concurrent_async_client.post(
        "/api/v1/user/backtests",
        json={
            "symbol": "VCB",
            "strategy_name": "Proprietary Algo",
            "strategy_type": "quant_momentum",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 500_000_000.0,
            "total_return": 0.42,
            "sharpe_ratio": 2.15,
            "max_drawdown": -0.04,
            "win_rate": 0.72,
            "equity_curve": [{"date": "2023-01-01", "equity": 500_000_000.0}],
        },
        headers=headers_a,
    )
    assert bt_a_res.status_code == 201
    bt_a = bt_a_res.json()
    bt_a_id = bt_a["id"]

    # Step 3: User B attempts to view User A's resources via collection GET
    b_wl_res = await concurrent_async_client.get("/api/v1/user/watchlists", headers=headers_b)
    assert b_wl_res.status_code == 200
    b_wl_items = b_wl_res.json()
    assert not any(w["id"] == wl_a_id for w in b_wl_items)

    b_preset_res = await concurrent_async_client.get("/api/v1/user/presets", headers=headers_b)
    assert b_preset_res.status_code == 200
    b_preset_items = b_preset_res.json()
    assert not any(p["id"] == preset_a_id for p in b_preset_items)

    b_bt_res = await concurrent_async_client.get("/api/v1/user/backtests", headers=headers_b)
    assert b_bt_res.status_code == 200
    b_bt_items = b_bt_res.json()
    assert not any(b["id"] == bt_a_id for b in b_bt_items)

    # Step 4: User B attempts direct GET by ID (should return 404 or 405, strictly NO 200 data leakage)
    direct_wl_res = await concurrent_async_client.get(
        f"/api/v1/user/watchlists/{wl_a_id}", headers=headers_b
    )
    assert direct_wl_res.status_code in (404, 405), (
        f"Unexpected status: {direct_wl_res.status_code}"
    )

    direct_preset_res = await concurrent_async_client.get(
        f"/api/v1/user/presets/{preset_a_id}", headers=headers_b
    )
    assert direct_preset_res.status_code in (404, 405), (
        f"Unexpected status: {direct_preset_res.status_code}"
    )

    # Step 5: User B attempts IDOR DELETE on User A's watchlist -> MUST return 404
    del_wl_res = await concurrent_async_client.delete(
        f"/api/v1/user/watchlists/{wl_a_id}", headers=headers_b
    )
    assert del_wl_res.status_code == 404, f"IDOR vulnerability! Status: {del_wl_res.status_code}"
    assert del_wl_res.json()["detail"] == "Watchlist not found"

    # Step 6: User B attempts IDOR DELETE on User A's strategy preset -> MUST return 404
    del_preset_res = await concurrent_async_client.delete(
        f"/api/v1/user/presets/{preset_a_id}", headers=headers_b
    )
    assert del_preset_res.status_code == 404, (
        f"IDOR vulnerability! Status: {del_preset_res.status_code}"
    )
    assert del_preset_res.json()["detail"] == "Strategy preset not found"

    # Step 7: Verify User A's resources are 100% intact
    check_wl_a = (
        await concurrent_async_client.get("/api/v1/user/watchlists", headers=headers_a)
    ).json()
    assert any(w["id"] == wl_a_id for w in check_wl_a)

    check_preset_a = (
        await concurrent_async_client.get("/api/v1/user/presets", headers=headers_a)
    ).json()
    assert any(p["id"] == preset_a_id for p in check_preset_a)

    check_bt_a = (
        await concurrent_async_client.get("/api/v1/user/backtests", headers=headers_a)
    ).json()
    assert any(b["id"] == bt_a_id for b in check_bt_a)


@pytest.mark.asyncio
async def test_adversarial_privilege_injection_user_id_tampering(
    concurrent_async_client: httpx.AsyncClient,
):
    """Stress Test: Attacker passing forged user_id in payload cannot plant records into another user's account."""
    user_a, token_a = await _register_and_login_helper(concurrent_async_client, "victim_a")
    _user_b, token_b = await _register_and_login_helper(concurrent_async_client, "attacker_b")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Attacker B creates watchlist explicitly injecting User A's UUID
    injected_payload = {
        "user_id": user_a["id"],
        "name": "Trojan Horse Watchlist",
        "symbols": ["VNM"],
    }
    create_res = await concurrent_async_client.post(
        "/api/v1/user/watchlists",
        json=injected_payload,
        headers=headers_b,
    )
    assert create_res.status_code == 201

    # Victim A must NOT see the injected watchlist
    a_watchlists = (
        await concurrent_async_client.get("/api/v1/user/watchlists", headers=headers_a)
    ).json()
    assert not any(w["name"] == "Trojan Horse Watchlist" for w in a_watchlists)

    # Attacker B sees it under B's account
    b_watchlists = (
        await concurrent_async_client.get("/api/v1/user/watchlists", headers=headers_b)
    ).json()
    assert any(w["name"] == "Trojan Horse Watchlist" for w in b_watchlists)


# =============================================================================
# 2. Tampered & Malicious UUIDs
# =============================================================================


@pytest.mark.asyncio
async def test_adversarial_nil_and_non_existent_uuid(
    concurrent_async_client: httpx.AsyncClient,
):
    """Stress Test: Nil UUID and random non-existent UUIDs return 404 without crashing."""
    _, token = await _register_and_login_helper(concurrent_async_client, "uuid_user")
    headers = {"Authorization": f"Bearer {token}"}

    nil_uuid = "00000000-0000-0000-0000-000000000000"
    random_uuid = str(uuid.uuid4())

    for bad_id in (nil_uuid, random_uuid):
        # Watchlists
        res_wl = await concurrent_async_client.delete(
            f"/api/v1/user/watchlists/{bad_id}", headers=headers
        )
        assert res_wl.status_code == 404
        assert res_wl.json()["detail"] == "Watchlist not found"

        # Presets
        res_preset = await concurrent_async_client.delete(
            f"/api/v1/user/presets/{bad_id}", headers=headers
        )
        assert res_preset.status_code == 404
        assert res_preset.json()["detail"] == "Strategy preset not found"


@pytest.mark.asyncio
async def test_adversarial_malformed_and_injection_uuids(
    concurrent_async_client: httpx.AsyncClient,
):
    """Stress Test: SQL injection, path traversal, and malformed strings in UUID path parameters."""
    _, token = await _register_and_login_helper(concurrent_async_client, "injection_user")
    headers = {"Authorization": f"Bearer {token}"}

    malicious_payloads = [
        "not-a-valid-uuid",
        "00000000-0000-0000-0000-00000000000g",  # non-hex char
        "00000000-0000-0000-0000",  # truncated
        "00000000-0000-0000-0000-0000000000000000",  # oversized
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "UNION SELECT * FROM users",
        "../../etc/passwd",
        "%00%2e%2e%2f",
        "123456789",
        "None",
        "null",
        "undefined",
        "NaN",
        "a" * 500,  # buffer stress
    ]

    for payload in malicious_payloads:
        # Watchlist delete
        res_wl = await concurrent_async_client.delete(
            f"/api/v1/user/watchlists/{payload}", headers=headers
        )
        # 404 (Not Found), 422 (Unprocessable), or 307 (Path traversal redirect) - NEVER 500 or 200
        assert res_wl.status_code in (404, 422, 307), (
            f"Failed on watchlist payload '{payload}': status {res_wl.status_code}"
        )

        # Preset delete
        res_preset = await concurrent_async_client.delete(
            f"/api/v1/user/presets/{payload}", headers=headers
        )
        assert res_preset.status_code in (404, 422, 307), (
            f"Failed on preset payload '{payload}': status {res_preset.status_code}"
        )


# =============================================================================
# 3. Massive Concurrent Multi-User Portfolio Requests (10 Virtual Users)
# =============================================================================


@pytest.mark.asyncio
async def test_adversarial_massive_concurrent_multi_user_isolation(
    concurrent_async_client: httpx.AsyncClient,
):
    """Stress Test: 10 virtual users simultaneously execute mutations and queries with zero crosstalk."""
    num_users = 10

    # 1. Register and login 10 virtual users concurrently
    async def create_virtual_user(idx: int) -> tuple[int, dict, str]:
        user_data, token = await _register_and_login_helper(
            concurrent_async_client, f"vuser_{idx}"
        )
        return idx, user_data, token

    users = await asyncio.gather(*[create_virtual_user(i) for i in range(num_users)])
    # Sort by index
    users.sort(key=lambda x: x[0])

    # 2. Concurrently create 3 watchlists, 3 presets, 2 backtests per user
    user_created_wls: dict[int, list[str]] = {i: [] for i in range(num_users)}
    user_created_presets: dict[int, list[str]] = {i: [] for i in range(num_users)}
    user_created_bts: dict[int, list[str]] = {i: [] for i in range(num_users)}

    async def populate_user_portfolio(idx: int, token: str):
        headers = {"Authorization": f"Bearer {token}"}

        # Create 3 watchlists
        for w_i in range(3):
            res = await concurrent_async_client.post(
                "/api/v1/user/watchlists",
                json={
                    "name": f"Watchlist_U{idx}_{w_i}",
                    "symbols": [f"SYM_{idx}_{w_i}_A", f"SYM_{idx}_{w_i}_B"],
                },
                headers=headers,
            )
            assert res.status_code == 201
            user_created_wls[idx].append(res.json()["id"])

        # Create 3 presets
        for p_i in range(3):
            res = await concurrent_async_client.post(
                "/api/v1/user/presets",
                json={
                    "name": f"Preset_U{idx}_{p_i}",
                    "parameters": {"user_idx": idx, "preset_idx": p_i, "stop": 0.05 * (p_i + 1)},
                },
                headers=headers,
            )
            assert res.status_code == 201
            user_created_presets[idx].append(res.json()["id"])

        # Create 2 backtests
        for b_i in range(2):
            res = await concurrent_async_client.post(
                "/api/v1/user/backtests",
                json={
                    "symbol": f"SYM_{idx}_{b_i}",
                    "strategy_name": f"Strategy_U{idx}_{b_i}",
                    "strategy_type": "ai_ensemble",
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "initial_capital": 100_000_000.0 * (idx + 1),
                    "total_return": 0.10 * (idx + 1),
                    "sharpe_ratio": 1.5,
                    "max_drawdown": -0.05,
                    "win_rate": 0.60,
                    "equity_curve": [{"date": "2023-01-01", "equity": 100_000_000.0}],
                },
                headers=headers,
            )
            assert res.status_code == 201
            user_created_bts[idx].append(res.json()["id"])

    # Launch all 10 user creations simultaneously
    await asyncio.gather(*[populate_user_portfolio(idx, token) for idx, _, token in users])

    # 3. Concurrent verification: Each user lists their resources simultaneously
    async def verify_isolation(idx: int, token: str):
        headers = {"Authorization": f"Bearer {token}"}

        # Check watchlists
        w_res = await concurrent_async_client.get("/api/v1/user/watchlists", headers=headers)
        assert w_res.status_code == 200
        w_items = w_res.json()
        assert len(w_items) == 3
        retrieved_w_ids = {w["id"] for w in w_items}
        assert retrieved_w_ids == set(user_created_wls[idx])

        # Check presets
        p_res = await concurrent_async_client.get("/api/v1/user/presets", headers=headers)
        assert p_res.status_code == 200
        p_items = p_res.json()
        assert len(p_items) == 3
        retrieved_p_ids = {p["id"] for p in p_items}
        assert retrieved_p_ids == set(user_created_presets[idx])

        # Check backtests
        b_res = await concurrent_async_client.get("/api/v1/user/backtests", headers=headers)
        assert b_res.status_code == 200
        b_items = b_res.json()
        assert len(b_items) == 2
        retrieved_b_ids = {b["id"] for b in b_items}
        assert retrieved_b_ids == set(user_created_bts[idx])

        # Confirm ZERO overlap with any other user's items
        for other_idx in range(num_users):
            if other_idx != idx:
                assert not any(w_id in retrieved_w_ids for w_id in user_created_wls[other_idx])
                assert not any(p_id in retrieved_p_ids for p_id in user_created_presets[other_idx])
                assert not any(b_id in retrieved_b_ids for b_id in user_created_bts[other_idx])

    # Launch all 10 user list queries simultaneously
    await asyncio.gather(*[verify_isolation(idx, token) for idx, _, token in users])

    # 4. Concurrent cross-tenant attack simulation:
    # User i simultaneously attempts to DELETE User (i+1)%10's watchlist and preset
    async def cross_tenant_delete_attack(idx: int, token: str):
        headers = {"Authorization": f"Bearer {token}"}
        target_idx = (idx + 1) % num_users
        target_wl_id = user_created_wls[target_idx][0]
        target_preset_id = user_created_presets[target_idx][0]

        del_w = await concurrent_async_client.delete(
            f"/api/v1/user/watchlists/{target_wl_id}", headers=headers
        )
        assert del_w.status_code == 404, (
            f"Cross-tenant deletion breach by user {idx} against {target_idx}"
        )

        del_p = await concurrent_async_client.delete(
            f"/api/v1/user/presets/{target_preset_id}", headers=headers
        )
        assert del_p.status_code == 404, (
            f"Cross-tenant deletion breach by user {idx} against {target_idx}"
        )

    await asyncio.gather(*[cross_tenant_delete_attack(idx, token) for idx, _, token in users])

    # 5. Legitimate deletions: each user deletes their 1st watchlist and 1st preset
    async def legitimate_delete(idx: int, token: str):
        headers = {"Authorization": f"Bearer {token}"}
        own_wl_id = user_created_wls[idx][0]
        own_preset_id = user_created_presets[idx][0]

        del_w = await concurrent_async_client.delete(
            f"/api/v1/user/watchlists/{own_wl_id}", headers=headers
        )
        assert del_w.status_code == 204

        del_p = await concurrent_async_client.delete(
            f"/api/v1/user/presets/{own_preset_id}", headers=headers
        )
        assert del_p.status_code == 204

    await asyncio.gather(*[legitimate_delete(idx, token) for idx, _, token in users])

    # 6. Final state verification: each user now has exactly 2 watchlists and 2 presets
    async def verify_final_state(idx: int, token: str):
        headers = {"Authorization": f"Bearer {token}"}
        w_items = (
            await concurrent_async_client.get("/api/v1/user/watchlists", headers=headers)
        ).json()
        assert len(w_items) == 2
        p_items = (
            await concurrent_async_client.get("/api/v1/user/presets", headers=headers)
        ).json()
        assert len(p_items) == 2

    await asyncio.gather(*[verify_final_state(idx, token) for idx, _, token in users])


# =============================================================================
# 4. Authentication Security Edge Cases & Token Isolation
# =============================================================================


@pytest.mark.asyncio
async def test_adversarial_token_type_confusion_rejects_refresh_token(
    concurrent_async_client: httpx.AsyncClient,
):
    """Stress Test: Supplying a Refresh Token in Authorization header must be rejected with 401."""
    user, _ = await _register_and_login_helper(concurrent_async_client, "type_user")
    refresh_token = create_refresh_token(subject=user["id"])

    # Attempt to access protected endpoint using refresh token
    res = await concurrent_async_client.get(
        "/api/v1/user/watchlists",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert res.status_code == 401
    assert "Invalid token type" in res.json()["detail"]


@pytest.mark.asyncio
async def test_adversarial_tampered_jwt_signature(
    concurrent_async_client: httpx.AsyncClient,
):
    """Stress Test: Tampering with JWT signature or payload causes immediate 401 rejection."""
    _, token = await _register_and_login_helper(concurrent_async_client, "tamper_user")
    parts = token.split(".")
    assert len(parts) == 3

    # Tamper with signature
    tampered_signature = parts[0] + "." + parts[1] + "." + parts[2][:-4] + "abcd"
    res1 = await concurrent_async_client.get(
        "/api/v1/user/watchlists",
        headers={"Authorization": f"Bearer {tampered_signature}"},
    )
    assert res1.status_code == 401

    # Tamper with payload (modify subject)
    tampered_payload = parts[0] + "." + parts[1][:-2] + "AA." + parts[2]
    res2 = await concurrent_async_client.get(
        "/api/v1/user/watchlists",
        headers={"Authorization": f"Bearer {tampered_payload}"},
    )
    assert res2.status_code == 401


@pytest.mark.asyncio
async def test_adversarial_inactive_user_access_blocked(
    concurrent_async_client: httpx.AsyncClient,
    db_engine: AsyncEngine,
):
    """Stress Test: Deactivated/banned user (is_active=False) cannot access any personal data."""
    user, token = await _register_and_login_helper(concurrent_async_client, "banned_user")
    headers = {"Authorization": f"Bearer {token}"}

    # Verify user can access initially
    res_init = await concurrent_async_client.get("/api/v1/user/watchlists", headers=headers)
    assert res_init.status_code == 200

    # Deactivate user directly in DB
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        db_user = await session.get(User, uuid.UUID(user["id"]))
        assert db_user is not None
        db_user.is_active = False
        await session.commit()

    # Attempt access with existing valid token -> MUST return 400 Inactive user account
    res_banned = await concurrent_async_client.get("/api/v1/user/watchlists", headers=headers)
    assert res_banned.status_code == 400
    assert "Inactive user account" in res_banned.json()["detail"]
