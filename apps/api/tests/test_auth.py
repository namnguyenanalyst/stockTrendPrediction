"""Unit & Integration tests cho Router Xác thực (/api/v1/auth)."""

import uuid
from datetime import timedelta

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.models.user import User


@pytest.mark.asyncio
async def test_register_balanced_default(async_client: httpx.AsyncClient):
    """Đăng ký tài khoản với các thông số mặc định (risk_profile='balanced', role='trader')."""
    uid = uuid.uuid4().hex[:8]
    email = f"balanced_{uid}@quant.vn"
    res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SafePassword@123"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == email
    assert data["risk_profile"] == "balanced"
    assert data["role"] == "trader"
    assert data["is_active"] is True
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_conservative_and_aggressive_profiles(async_client: httpx.AsyncClient):
    """Đăng ký tài khoản với khẩu vị conservative và aggressive."""
    uid1 = uuid.uuid4().hex[:8]
    res1 = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"cons_{uid1}@quant.vn",
            "password": "SafePassword@123",
            "risk_profile": "conservative",
        },
    )
    assert res1.status_code == 201
    assert res1.json()["risk_profile"] == "conservative"

    uid2 = uuid.uuid4().hex[:8]
    res2 = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"aggr_{uid2}@quant.vn",
            "password": "SafePassword@123",
            "risk_profile": "aggressive",
        },
    )
    assert res2.status_code == 201
    assert res2.json()["risk_profile"] == "aggressive"


@pytest.mark.asyncio
async def test_register_with_vietnamese_fullname(async_client: httpx.AsyncClient):
    """Đăng ký tài khoản với họ và tên tiếng Việt có dấu chuẩn UTF-8."""
    uid = uuid.uuid4().hex[:8]
    full_name = "Nguyễn Văn Hùng Lộc"
    res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"vn_{uid}@quant.vn",
            "password": "SafePassword@123",
            "full_name": full_name,
        },
    )
    assert res.status_code == 201
    assert res.json()["full_name"] == full_name


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_400(async_client: httpx.AsyncClient):
    """Đăng ký trùng email trả về HTTP 400 Bad Request."""
    uid = uuid.uuid4().hex[:8]
    email = f"dup_{uid}@quant.vn"
    res1 = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SafePassword@123"},
    )
    assert res1.status_code == 201

    res2 = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SafePassword@123"},
    )
    assert res2.status_code == 400
    assert "already registered" in res2.text.lower()


@pytest.mark.asyncio
async def test_register_duplicate_email_case_insensitive(async_client: httpx.AsyncClient):
    """Đăng ký trùng email không phân biệt chữ hoa/chữ thường trả về 400."""
    uid = uuid.uuid4().hex[:8]
    email = f"case_{uid}@quant.vn"
    res1 = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email.lower(), "password": "SafePassword@123"},
    )
    assert res1.status_code == 201

    res2 = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email.upper(), "password": "SafePassword@123"},
    )
    assert res2.status_code == 400


@pytest.mark.asyncio
async def test_register_invalid_email_missing_at_returns_422(async_client: httpx.AsyncClient):
    """Đăng ký email thiếu ký tự @ trả về 422."""
    res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "invalid_email_without_at.vn", "password": "SafePassword@123"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email_missing_domain_returns_422(async_client: httpx.AsyncClient):
    """Đăng ký email thiếu tên miền cấp cao trả về 422."""
    res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "user@nodomain", "password": "SafePassword@123"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password_returns_422(async_client: httpx.AsyncClient):
    """Đăng ký mật khẩu dưới 8 ký tự trả về 422."""
    res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "short@quant.vn", "password": "short"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_risk_profile_returns_422(async_client: httpx.AsyncClient):
    """Đăng ký với khẩu vị rủi ro không hỗ trợ trả về 422."""
    res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "bad_risk@quant.vn",
            "password": "SafePassword@123",
            "risk_profile": "ultra_speculator",
        },
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_login_valid_credentials(async_client: httpx.AsyncClient):
    """Đăng nhập thành công trả về access token và thông tin người dùng."""
    uid = uuid.uuid4().hex[:8]
    email = f"login_{uid}@quant.vn"
    pwd = "ValidPassword@123"
    await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd})

    res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert len(data["access_token"]) > 20
    assert data["token_type"].lower() == "bearer"
    assert data["user"]["email"] == email


@pytest.mark.asyncio
async def test_login_sets_refresh_cookie_attributes(async_client: httpx.AsyncClient):
    """Đăng nhập thiết lập cookie refresh_token với thuộc tính HttpOnly và Path=/api/v1/auth."""
    uid = uuid.uuid4().hex[:8]
    email = f"cookie_{uid}@quant.vn"
    pwd = "ValidPassword@123"
    await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd})

    res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert res.status_code == 200
    cookie_str = res.headers.get("set-cookie", "").lower()
    assert "refresh_token=" in cookie_str
    assert "httponly" in cookie_str
    assert "path=/api/v1/auth" in cookie_str


@pytest.mark.asyncio
async def test_login_case_insensitive_email(async_client: httpx.AsyncClient):
    """Đăng nhập email viết hoa khớp với email đăng ký viết thường."""
    uid = uuid.uuid4().hex[:8]
    email = f"upper_{uid}@quant.vn"
    pwd = "ValidPassword@123"
    await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd})

    res = await async_client.post(
        "/api/v1/auth/login", json={"email": email.upper(), "password": pwd}
    )
    assert res.status_code == 200
    assert res.json()["user"]["email"] == email.lower()


@pytest.mark.asyncio
async def test_login_nonexistent_email_returns_401(async_client: httpx.AsyncClient):
    """Đăng nhập email không tồn tại trả về 401 Unauthorized."""
    res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent_9999@quant.vn", "password": "SomePassword@123"},
    )
    assert res.status_code == 401
    assert "incorrect" in res.text.lower()


@pytest.mark.asyncio
async def test_login_incorrect_password_returns_401(async_client: httpx.AsyncClient):
    """Đăng nhập sai mật khẩu trả về 401."""
    uid = uuid.uuid4().hex[:8]
    email = f"wrong_pwd_{uid}@quant.vn"
    await async_client.post(
        "/api/v1/auth/register", json={"email": email, "password": "CorrectPassword@123"}
    )

    res = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "WrongPassword@999"}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user_returns_400(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    """Người dùng bị khóa (is_active=False) đăng nhập bị trả về HTTP 400."""
    uid = uuid.uuid4().hex[:8]
    email = f"inactive_{uid}@quant.vn"
    pwd = "ValidPassword@123"
    await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd})

    # Vô hiệu hóa tài khoản trong database
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.is_active = False
    await db_session.commit()

    res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert res.status_code == 400
    assert "inactive" in res.text.lower()


@pytest.mark.asyncio
async def test_refresh_token_via_cookie(async_client: httpx.AsyncClient):
    """Cấp mới Access Token bằng cookie refresh_token."""
    uid = uuid.uuid4().hex[:8]
    email = f"ref_cookie_{uid}@quant.vn"
    pwd = "ValidPassword@123"
    await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd})

    login_res = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": pwd}
    )
    assert login_res.cookies.get("refresh_token") is not None

    # Yêu cầu refresh sử dụng cookie vừa nhận từ login
    res = await async_client.post("/api/v1/auth/refresh")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert len(data["access_token"]) > 20


@pytest.mark.asyncio
async def test_refresh_token_via_body(async_client: httpx.AsyncClient):
    """Cấp mới Access Token bằng JSON body chứa refresh_token."""
    uid = uuid.uuid4().hex[:8]
    email = f"ref_body_{uid}@quant.vn"
    pwd = "ValidPassword@123"
    await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd})

    login_res = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": pwd}
    )
    refresh_cookie = login_res.cookies.get("refresh_token")

    # Xóa cookie trên client để đảm bảo request chỉ dựa vào body
    async_client.cookies.clear()

    res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_cookie},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_refresh_missing_token_returns_401(async_client: httpx.AsyncClient):
    """Yêu cầu /refresh không có cookie và body trả về 401."""
    async_client.cookies.clear()
    res = await async_client.post("/api/v1/auth/refresh", json={})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_refresh_invalid_token_returns_401(async_client: httpx.AsyncClient):
    """Yêu cầu /refresh với token rác trả về 401."""
    async_client.cookies.clear()
    res = await async_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "corrupt_token_string"}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_refresh_wrong_token_type_returns_401(async_client: httpx.AsyncClient):
    """Gửi Access Token vào endpoint refresh trả về 401 vì sai token type."""
    uid = uuid.uuid4().hex[:8]
    email = f"wrong_type_{uid}@quant.vn"
    pwd = "ValidPassword@123"
    await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
    login_res = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": pwd}
    )
    access_token = login_res.json()["access_token"]

    async_client.cookies.clear()
    res = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_success(async_client: httpx.AsyncClient):
    """GET /api/v1/auth/me trả về đúng thông tin user của token hợp lệ."""
    uid = uuid.uuid4().hex[:8]
    email = f"me_{uid}@quant.vn"
    pwd = "ValidPassword@123"
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": pwd,
            "full_name": "Test Trader",
            "risk_profile": "aggressive",
        },
    )
    login_res = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": pwd}
    )
    token = login_res.json()["access_token"]

    res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == email
    assert data["full_name"] == "Test Trader"
    assert data["risk_profile"] == "aggressive"
    assert data["role"] == "trader"
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_get_me_missing_auth_header_returns_401(async_client: httpx.AsyncClient):
    """GET /api/v1/auth/me không có header Authorization trả về 401."""
    res = await async_client.get("/api/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_tampered_token_returns_401(async_client: httpx.AsyncClient):
    """GET /api/v1/auth/me với token bị can thiệp chữ ký trả về 401."""
    token = create_access_token("some-id")
    tampered = token[:-6] + "ABCDEF"
    res = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered}"}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_expired_token_returns_401(async_client: httpx.AsyncClient):
    """GET /api/v1/auth/me với token đã hết hạn trả về 401."""
    expired_token = create_access_token("some-id", expires_delta=timedelta(seconds=-10))
    res = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert res.status_code == 401
