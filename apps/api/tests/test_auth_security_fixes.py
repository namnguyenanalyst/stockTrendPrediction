"""Tests for security audit fixes: login/register rate limits, sole admin forgot-password, cookie origin."""

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models.user import User, UserRole


@pytest.mark.asyncio
async def test_login_rate_limit_blocks_brute_force(async_client: AsyncClient):
    """Login quá 10 lần/phút cùng email+IP phải bị chặn với 429 và Retry-After."""
    for i in range(10):
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "victim@example.com", "password": f"wrong-{i}"},
        )
        assert res.status_code == 401

    blocked = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "victim@example.com", "password": "wrong-final"},
    )
    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After") == "60"


@pytest.mark.asyncio
async def test_register_rate_limit_runs_before_duplicate_email_check(
    async_client: AsyncClient, db_session
):
    """Spam /register với email đã tồn tại vẫn phải bị rate limit 429 (chống enumeration)."""
    user = User(
        email="existing@example.com",
        hashed_password=get_password_hash("StrongPass123!"),
        role=UserRole.TRADER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    for _ in range(10):
        res = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "existing@example.com", "password": "StrongPass123!"},
        )
        assert res.status_code == 400

    blocked = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "existing@example.com", "password": "StrongPass123!"},
    )
    assert blocked.status_code == 429


@pytest.mark.asyncio
async def test_forgot_password_accepts_sole_admin_internal_email(async_client: AsyncClient):
    """SOLE_ADMIN_EMAIL (admin@vnstock) không có dấu chấm domain vẫn hợp lệ ở forgot-password."""
    res = await async_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": settings.SOLE_ADMIN_EMAIL},
    )
    assert res.status_code == 202


@pytest.mark.asyncio
async def test_cookie_auth_origin_and_referer_matrix(
    async_client: AsyncClient,
):
    """Kiểm tra đủ các trường hợp Origin và Referer trong check_cookie_origin()."""
    async_client.cookies.set("refresh_token", "dummy-token")

    # 1. Origin hợp lệ -> vượt qua check_cookie_origin (trả 401 do dummy token, không phải 403)
    res_valid_origin = await async_client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:3000"},
    )
    assert res_valid_origin.status_code == 401

    # 2. Origin sai -> 403
    res_bad_origin = await async_client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "https://evil.example.com"},
    )
    assert res_bad_origin.status_code == 403

    # 3. Thiếu Origin + Referer hợp lệ -> vượt qua check_cookie_origin
    res_valid_referer = await async_client.post(
        "/api/v1/auth/refresh",
        headers={"Referer": "http://localhost:3000/dashboard?tab=1"},
    )
    assert res_valid_referer.status_code == 401

    # 4. Thiếu Origin + Referer giả mạo tiền tố domain -> 403
    res_prefix_spoof = await async_client.post(
        "/api/v1/auth/refresh",
        headers={"Referer": "http://localhost:3000.evil.com/phish"},
    )
    assert res_prefix_spoof.status_code == 403

    # 5. Thiếu cả Origin lẫn Referer -> tương thích client test (trả 401 do dummy token)
    res_neither = await async_client.post("/api/v1/auth/refresh")
    assert res_neither.status_code == 401
