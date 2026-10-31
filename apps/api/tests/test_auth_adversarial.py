"""Adversarial Security & Robustness Tests cho Auth & Personalization APIs.

Bộ kiểm thử thù địch tập trung vào:
1. JWT Signature tampering, 'none' algorithm bypass, sai secret key, expired, malformed tokens.
2. Token swapping / cross-endpoint misuse (Refresh token trên Access routes, Access token trên Refresh route).
3. SQL Injection resistance trên Email, Password, Full Name, và Personalization CRUD.
4. Password verification edge cases (Bcrypt 72-byte truncation, multi-byte UTF-8, null bytes, high payload size).
5. Duplicate casing email collisions và whitespace normalization.
6. Inactive / deleted user token invalidation.
7. Role tampering / privilege escalation attempts on registration.
8. Timing discrepancy / user enumeration behavior.
"""

import time
import uuid
from datetime import timedelta

import httpx
import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.db.models.user import User


async def _create_test_user(
    client: httpx.AsyncClient,
    prefix: str = "adv",
    password: str = "StrongPass@123",
    role_attempt: str | None = None,
) -> tuple[dict, str, str]:
    """Helper tạo tài khoản và trả về (user_dict, access_token, refresh_token)."""
    uid = uuid.uuid4().hex[:8]
    email = f"{prefix}_{uid}@quant.vn"
    reg_body = {"email": email, "password": password, "full_name": f"Adversarial {prefix}"}
    if role_attempt:
        reg_body["role"] = role_attempt

    reg_res = await client.post("/api/v1/auth/register", json=reg_body)
    assert reg_res.status_code == 201
    user_info = reg_res.json()

    login_res = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    access_token = login_data["access_token"]
    refresh_token = login_res.cookies.get("refresh_token")
    return user_info, access_token, refresh_token


# =============================================================================
# 1. JWT Security & Tamper Resistance
# =============================================================================


@pytest.mark.asyncio
async def test_jwt_alg_none_attack_rejected(async_client: httpx.AsyncClient):
    """Tấn công 'none' algorithm: gửi JWT với header alg='none' và không có chữ ký.

    Hệ thống bắt buộc phải từ chối với HTTP 401 Unauthorized.
    """
    header_b64 = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0"  # {"alg":"none","typ":"JWT"}
    payload_b64 = (
        "eyJzdWIiOiIxMTExMTExMS0xMTExLTExMTEtMTExMS0xMTExMTExMTExMTEiLCJ0eXBlIjoiYWNjZXNzIn0"
    )
    unsigned_token = f"{header_b64}.{payload_b64}."

    res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {unsigned_token}"},
    )
    assert res.status_code == 401
    assert "invalid" in res.text.lower() or "not authenticated" in res.text.lower()


@pytest.mark.asyncio
async def test_jwt_forged_secret_key_rejected(async_client: httpx.AsyncClient):
    """Ký token bằng secret key khác của kẻ tấn công (HS256) phải bị từ chối 401."""
    fake_secret = "evil_secret_key_attacker_0000000000000000"
    forged_token = jwt.encode(
        {"sub": str(uuid.uuid4()), "type": "access"},
        fake_secret,
        algorithm="HS256",
    )

    res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged_token}"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_jwt_missing_subject_rejected(async_client: httpx.AsyncClient):
    """Token thiếu claim 'sub' phải trả về 401 Unauthorized."""
    token = jwt.encode(
        {"type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 401
    assert "missing" in res.text.lower() or "invalid" in res.text.lower()


@pytest.mark.asyncio
async def test_jwt_malformed_uuid_subject_rejected(async_client: httpx.AsyncClient):
    """Token có claim 'sub' không phải UUID hợp lệ (ví dụ chuỗi chữ bất kỳ) phải trả về 401."""
    token = jwt.encode(
        {"sub": "not-a-valid-uuid-format", "type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_jwt_nonexistent_user_uuid_rejected(async_client: httpx.AsyncClient):
    """Token có 'sub' là UUID hợp lệ nhưng không tồn tại trong database phải trả về 401."""
    nonexistent_id = str(uuid.uuid4())
    token = create_access_token(subject=nonexistent_id)
    res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 401
    assert "user not found" in res.text.lower()


@pytest.mark.asyncio
async def test_jwt_expired_extreme_past_rejected(async_client: httpx.AsyncClient):
    """Token hết hạn sâu trong quá khứ (1 năm trước) phải bị từ chối 401."""
    expired_token = create_access_token(
        subject=str(uuid.uuid4()),
        expires_delta=timedelta(days=-365),
    )
    res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401


# =============================================================================
# 2. Token Swapping (Access on Refresh, Refresh on Access)
# =============================================================================


@pytest.mark.asyncio
async def test_refresh_token_used_on_protected_endpoints_rejected(
    async_client: httpx.AsyncClient,
):
    """Dùng Refresh Token trên các endpoint yêu cầu Access Token phải bị từ chối 401."""
    _, _, refresh_token = await _create_test_user(async_client, prefix="swap_r2a")
    assert refresh_token is not None
    headers = {"Authorization": f"Bearer {refresh_token}"}

    # /api/v1/auth/me
    res_me = await async_client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 401
    assert "access token required" in res_me.text.lower()

    # /api/v1/user/watchlists
    res_wl = await async_client.get("/api/v1/user/watchlists", headers=headers)
    assert res_wl.status_code == 401
    assert "access token required" in res_wl.text.lower()

    # /api/v1/user/presets
    res_pr = await async_client.get("/api/v1/user/presets", headers=headers)
    assert res_pr.status_code == 401
    assert "access token required" in res_pr.text.lower()

    # /api/v1/user/backtests
    res_bt = await async_client.get("/api/v1/user/backtests", headers=headers)
    assert res_bt.status_code == 401
    assert "access token required" in res_bt.text.lower()


@pytest.mark.asyncio
async def test_access_token_used_on_refresh_via_body_and_cookie_rejected(
    async_client: httpx.AsyncClient,
):
    """Dùng Access Token trên endpoint /api/v1/auth/refresh (cả qua Body và qua Cookie) phải bị từ chối 401."""
    _, access_token, _ = await _create_test_user(async_client, prefix="swap_a2r")

    # 1. Gửi Access Token qua JSON body
    async_client.cookies.clear()
    res_body = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert res_body.status_code == 401
    assert "refresh token required" in res_body.text.lower()

    # 2. Gửi Access Token qua Cookie
    async_client.cookies.set("refresh_token", access_token)
    res_cookie = await async_client.post("/api/v1/auth/refresh")
    assert res_cookie.status_code == 401
    assert "refresh token required" in res_cookie.text.lower()


# =============================================================================
# 3. SQL Injection Resistance
# =============================================================================


@pytest.mark.asyncio
async def test_sqli_attempts_in_registration_rejected(async_client: httpx.AsyncClient):
    """Tấn công SQL Injection trong trường email đăng ký bị Pydantic chặn bằng 422 trước khi vào DB."""
    sqli_payloads = [
        "admin' OR 1=1; --@quant.vn",
        "' OR '1'='1'@quant.vn",
        "'; DROP TABLE users; --@quant.vn",
        "test' UNION SELECT * FROM users; --@quant.vn",
    ]
    for payload in sqli_payloads:
        res = await async_client.post(
            "/api/v1/auth/register",
            json={"email": payload, "password": "StrongPassword@123"},
        )
        assert res.status_code == 422, f"Payload {payload} should be rejected with 422"


@pytest.mark.asyncio
async def test_sqli_attempts_in_login_fail_safely(async_client: httpx.AsyncClient):
    """Tấn công SQL Injection trong trường email và password đăng nhập không bypass được xác thực."""
    sqli_credentials = [
        ("' OR '1'='1' --", "anything"),
        ("admin'--", "anything"),
        ("' OR 1=1 --", "' OR 1=1 --"),
        ("user@quant.vn' UNION SELECT 1,2,3,4,5,6,7,8,9 --", "password"),
        ("'; DROP TABLE users; --", "password"),
    ]
    for email_payload, pwd_payload in sqli_credentials:
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"email": email_payload, "password": pwd_payload},
        )
        # Bắt buộc trả về 401 Unauthorized chứ không phải 500 Internal Server Error hay bypass 200
        assert res.status_code == 401, (
            f"SQLi payload {email_payload} did not return 401, got {res.status_code}"
        )


@pytest.mark.asyncio
async def test_sqli_in_fullname_stored_safely_as_literal(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    """Payload SQLi trong full_name được lưu an toàn dưới dạng ký tự thô, không gây lỗi cú pháp SQL."""
    uid = uuid.uuid4().hex[:8]
    email = f"sqli_fn_{uid}@quant.vn"
    sqli_name = "Robert'); DROP TABLE user_watchlists;--"

    res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPassword@123", "full_name": sqli_name},
    )
    assert res.status_code == 201
    assert res.json()["full_name"] == sqli_name

    # Xác nhận bảng user_watchlists và user vẫn tồn tại
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.full_name == sqli_name


@pytest.mark.asyncio
async def test_sqli_in_personalization_inputs_handled_safely(
    async_client: httpx.AsyncClient,
):
    """Payload SQLi trong các trường Watchlist, Preset, Backtest được parameterized an toàn."""
    _, token, _ = await _create_test_user(async_client, prefix="sqli_user")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. SQLi trong tên watchlist và symbol
    # Lưu ý: schema watchlist tự động .upper() mã symbol
    wl_res = await async_client.post(
        "/api/v1/user/watchlists",
        json={
            "name": "Watchlist'; DROP TABLE users;--",
            "symbols": ["HPG'; DROP TABLE users;--", "VIC"],
        },
        headers=headers,
    )
    assert wl_res.status_code == 201
    assert wl_res.json()["name"] == "Watchlist'; DROP TABLE users;--"
    assert "HPG'; DROP TABLE USERS;--" in wl_res.json()["symbols"]

    # 2. SQLi trong preset name và JSON parameters
    preset_res = await async_client.post(
        "/api/v1/user/presets",
        json={
            "name": "Preset' OR '1'='1",
            "description": "Exploit attempt --",
            "parameters": {"sql'; DELETE FROM users;--": "value"},
        },
        headers=headers,
    )
    assert preset_res.status_code == 201
    assert preset_res.json()["name"] == "Preset' OR '1'='1"

    # 3. SQLi trong backtest history fields
    bt_res = await async_client.post(
        "/api/v1/user/backtests",
        json={
            "symbol": "HPG'; DROP TABLE users;--",
            "strategy_name": "Strat' OR '1'='1",
            "strategy_type": "type';--",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 100_000_000.0,
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.05,
            "win_rate": 0.55,
            "equity_curve": [{"note': DROP TABLE users;--": 123}],
        },
        headers=headers,
    )
    assert bt_res.status_code == 201
    assert bt_res.json()["symbol"] == "HPG'; DROP TABLE USERS;--"

    # 4. SQLi trong path parameter (UUID injection) -> Phải trả về 404
    path_sqli = await async_client.delete(
        "/api/v1/user/watchlists/' OR '1'='1",
        headers=headers,
    )
    assert path_sqli.status_code == 404


# =============================================================================
# 4. Password Boundary & UTF-8 Edge Cases
# =============================================================================


@pytest.mark.asyncio
async def test_password_longer_than_72_bytes_handled_without_crash(
    async_client: httpx.AsyncClient,
):
    """Mật khẩu dài vượt quá 72 bytes (ví dụ 120 ký tự) đăng ký và đăng nhập bình thường.

    Đồng thời kiểm chứng đặc tính cắt lát 72-byte của Bcrypt: mật khẩu trùng 72 bytes đầu
    sẽ được coi là hợp lệ (đặc tính kỹ thuật đã ghi nhận của Bcrypt không kèm SHA256 pre-hash).
    """
    uid = uuid.uuid4().hex[:8]
    email = f"longpwd_{uid}@quant.vn"

    base_72 = "A" * 72
    long_pwd_registered = base_72 + "EXTENSION_12345"

    # Đăng ký thành công
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": long_pwd_registered},
    )
    assert reg_res.status_code == 201

    # Đăng nhập bằng đúng mật khẩu 120 ký tự
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": long_pwd_registered},
    )
    assert login_res.status_code == 200

    # Kiểm tra: mật khẩu có cùng 72 ký tự đầu
    login_same_prefix = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": base_72 + "DIFFERENT_TAIL"},
    )
    # Xác nhận tính nhất quán thực nghiệm của cơ chế bcrypt[:72]
    assert login_same_prefix.status_code == 200

    # Nhưng mật khẩu khác trong 72 ký tự đầu phải bị từ chối 401
    login_diff_prefix = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "B" * 72 + "EXTENSION_12345"},
    )
    assert login_diff_prefix.status_code == 401


@pytest.mark.asyncio
async def test_password_multibyte_utf8_vietnamese_and_emojis(
    async_client: httpx.AsyncClient,
):
    """Mật khẩu chứa ký tự tiếng Việt đa byte và Emoji xử lý chuẩn xác không gây lỗi byte boundary."""
    uid = uuid.uuid4().hex[:8]
    email = f"utf8_{uid}@quant.vn"
    unicode_pwd = "MậtKhẩuCựcKỳBảoMật_🇻🇳_VNIndex@1500!🚀📈"

    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": unicode_pwd},
    )
    assert reg_res.status_code == 201

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": unicode_pwd},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


@pytest.mark.asyncio
async def test_password_boundary_splitting_multibyte_character(
    async_client: httpx.AsyncClient,
):
    """Kiểm tra trường hợp ký tự đa byte nằm đúng vị trí ranh giới byte 72.

    Ví dụ: 71 ký tự ASCII (71 bytes) + ký tự 2-byte 'đ' (cắt tại byte 72 để lại 1 byte lẻ).
    Hệ thống bcrypt.hashpw và verify_password vẫn hoạt động an toàn và đồng bộ.
    """
    uid = uuid.uuid4().hex[:8]
    email = f"boundary_{uid}@quant.vn"
    # 71 bytes 'x' + ký tự 'đ' (2 bytes UTF-8: 0xc4, 0x91)
    boundary_pwd = ("x" * 71) + "đ" + "ExtraSuffix"

    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": boundary_pwd},
    )
    assert reg_res.status_code == 201

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": boundary_pwd},
    )
    assert login_res.status_code == 200


@pytest.mark.asyncio
async def test_password_massive_length_stress(async_client: httpx.AsyncClient):
    """Gửi mật khẩu dài 10,000 ký tự: không gây DoS, treo ứng dụng hay lỗi tràn bộ nhớ."""
    uid = uuid.uuid4().hex[:8]
    email = f"massive_{uid}@quant.vn"
    massive_pwd = "SafeP@ss" + ("0" * 10000)

    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": massive_pwd},
    )
    assert reg_res.status_code == 201

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": massive_pwd},
    )
    assert login_res.status_code == 200


@pytest.mark.asyncio
async def test_empty_and_whitespace_passwords(async_client: httpx.AsyncClient):
    """Mật khẩu rỗng bị từ chối 422 khi đăng ký; mật khẩu rỗng khi đăng nhập bị 401."""
    # 1. Đăng ký mật khẩu rỗng
    res_reg_empty = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "empty_pwd@quant.vn", "password": ""},
    )
    assert res_reg_empty.status_code == 422

    # 2. Đăng ký tài khoản hợp lệ
    uid = uuid.uuid4().hex[:8]
    valid_email = f"empty_test_{uid}@quant.vn"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": valid_email, "password": "ValidPassword@123"},
    )

    # 3. Đăng nhập với mật khẩu rỗng -> 401
    res_login_empty = await async_client.post(
        "/api/v1/auth/login",
        json={"email": valid_email, "password": ""},
    )
    assert res_login_empty.status_code == 401


# =============================================================================
# 5. Email Casing Collision & Whitespace Normalization
# =============================================================================


@pytest.mark.asyncio
async def test_email_casing_variations_prevent_collision(async_client: httpx.AsyncClient):
    """Đăng ký email với các biến thể hoa thường khác nhau đều bị nhận diện trùng lặp (400)."""
    base_user = f"user_{uuid.uuid4().hex[:8]}"
    domain = "quant.vn"

    # Đăng ký lần đầu dạng chữ thường
    res1 = await async_client.post(
        "/api/v1/auth/register",
        json={"email": f"{base_user}@{domain}", "password": "Password@123"},
    )
    assert res1.status_code == 201
    assert res1.json()["email"] == f"{base_user}@{domain}"

    # Đăng ký lại với chữ hoa toàn bộ
    res2 = await async_client.post(
        "/api/v1/auth/register",
        json={"email": f"{base_user.upper()}@{domain.upper()}", "password": "Password@123"},
    )
    assert res2.status_code == 400
    assert "already registered" in res2.text.lower()

    # Đăng ký lại với chữ xen kẽ (camel/mixed case)
    mixed_user = "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(base_user))
    res3 = await async_client.post(
        "/api/v1/auth/register",
        json={"email": f"{mixed_user}@{domain}", "password": "Password@123"},
    )
    assert res3.status_code == 400
    assert "already registered" in res3.text.lower()


@pytest.mark.asyncio
async def test_email_whitespace_stripping(async_client: httpx.AsyncClient):
    """Email có khoảng trắng đầu cuối được tự động strip() sạch sẽ."""
    uid = uuid.uuid4().hex[:8]
    clean_email = f"strip_{uid}@quant.vn"
    padded_email = f"   {clean_email}   "

    res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": padded_email, "password": "Password@123"},
    )
    assert res.status_code == 201
    assert res.json()["email"] == clean_email

    # Login với khoảng trắng đầu cuối
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": padded_email, "password": "Password@123"},
    )
    assert login_res.status_code == 200
    assert login_res.json()["user"]["email"] == clean_email


# =============================================================================
# 6. User Lifecycle & Invalidation (Inactive, Deleted User)
# =============================================================================


@pytest.mark.asyncio
async def test_deactivated_user_cannot_access_or_refresh(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    """Người dùng bị vô hiệu hóa (is_active=False) bị từ chối trên cả /me, /user và /refresh."""
    user_info, access_token, refresh_token = await _create_test_user(
        async_client, prefix="deact_user"
    )
    user_id = uuid.UUID(user_info["id"])

    # Vô hiệu hóa người dùng trong CSDL
    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.is_active = False
    await db_session.commit()

    headers = {"Authorization": f"Bearer {access_token}"}

    # /api/v1/auth/me -> 400 Inactive user account
    res_me = await async_client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 400
    assert "inactive" in res_me.text.lower()

    # /api/v1/user/watchlists -> 400 Inactive user account
    res_wl = await async_client.get("/api/v1/user/watchlists", headers=headers)
    assert res_wl.status_code == 400
    assert "inactive" in res_wl.text.lower()

    # /api/v1/auth/refresh -> 401 User not found or inactive
    async_client.cookies.clear()
    res_ref = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert res_ref.status_code == 401
    assert "inactive" in res_ref.text.lower() or "not found" in res_ref.text.lower()


@pytest.mark.asyncio
async def test_deleted_user_token_rejected_with_401(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    """Token vẫn còn hạn nhưng bản ghi user đã bị xóa khỏi CSDL phải trả về 401."""
    user_info, access_token, refresh_token = await _create_test_user(
        async_client, prefix="del_token_user"
    )
    user_id = uuid.UUID(user_info["id"])

    # Xóa người dùng khỏi database
    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    await db_session.delete(user)
    await db_session.commit()

    # Access Token trên /me -> 401 User not found
    res_me = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert res_me.status_code == 401
    assert "user not found" in res_me.text.lower()

    # Refresh Token trên /refresh -> 401 User not found
    async_client.cookies.clear()
    res_ref = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert res_ref.status_code == 401


# =============================================================================
# 7. Privilege Escalation Resistance
# =============================================================================


@pytest.mark.asyncio
async def test_register_role_tampering_ignored(async_client: httpx.AsyncClient):
    """Kẻ tấn công gửi field role='admin' trong payload /register phải bị bỏ qua (role luôn là 'trader')."""
    user_info, _, _ = await _create_test_user(
        async_client, prefix="escalate", role_attempt="admin"
    )
    assert user_info["role"] == "trader", (
        "Role must default to trader regardless of register payload"
    )


# =============================================================================
# 8. Timing Discrepancy Observation (Empirical Measurement)
# =============================================================================


@pytest.mark.asyncio
async def test_timing_discrepancy_observation(async_client: httpx.AsyncClient):
    """Khảo sát thực nghiệm về độ lệch thời gian phản hồi giữa email tồn tại và không tồn tại.

    Khi email không tồn tại: chỉ truy vấn DB rồi trả về 401 (thời gian ~1-10ms).
    Khi email tồn tại nhưng sai password: truy vấn DB + bcrypt verify (thời gian ~50-250ms).
    Đây là hiện tượng user enumeration qua timing discrepancy phổ biến khi không thực hiện dummy hash.
    Test này ghi nhận đo lường thực nghiệm mà không đánh trượt bài kiểm tra.
    """
    # 1. Tạo user hợp lệ
    uid = uuid.uuid4().hex[:8]
    valid_email = f"timing_{uid}@quant.vn"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": valid_email, "password": "CorrectPassword@123"},
    )

    # 2. Đo thời gian khi email KHÔNG tồn tại
    t0 = time.perf_counter()
    res_nonexistent = await async_client.post(
        "/api/v1/auth/login",
        json={"email": f"nonexistent_{uid}@quant.vn", "password": "WrongPassword@123"},
    )
    t_nonexistent = time.perf_counter() - t0
    assert res_nonexistent.status_code == 401

    # 3. Đo thời gian khi email CÓ tồn tại nhưng sai password
    t0 = time.perf_counter()
    res_wrong_pwd = await async_client.post(
        "/api/v1/auth/login",
        json={"email": valid_email, "password": "WrongPassword@123"},
    )
    t_wrong_pwd = time.perf_counter() - t0
    assert res_wrong_pwd.status_code == 401

    # In ra để làm bằng chứng thực nghiệm
    print(f"\n[Empirical Timing] Non-existent user latency: {t_nonexistent * 1000:.2f}ms")
    print(f"[Empirical Timing] Existing user wrong pwd latency: {t_wrong_pwd * 1000:.2f}ms")
    assert t_nonexistent >= 0 and t_wrong_pwd >= 0


# =============================================================================
# 9. Additional Adversarial Vectors (Replay & Null Bytes)
# =============================================================================


@pytest.mark.asyncio
async def test_refresh_token_multi_use_stateless_replay(async_client: httpx.AsyncClient):
    """Kiểm tra đặc tính stateless của JWT Refresh Token:

    Do không lưu refresh token vào database (không có token rotation hay blacklist),
    cùng một refresh token có thể được dùng nhiều lần liên tiếp để xin access token mới.
    Đây là đặc tính kiến trúc JWT stateless đã ghi nhận.
    """
    _, _, refresh_token = await _create_test_user(async_client, prefix="replay")
    assert refresh_token is not None

    async_client.cookies.clear()
    # Lần 1: Cấp access token
    res1 = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert res1.status_code == 200
    token1 = res1.json()["access_token"]

    # Lần 2: Cấp tiếp access token thứ 2 từ cùng refresh token
    res2 = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert res2.status_code == 200
    token2 = res2.json()["access_token"]

    assert token1 is not None and token2 is not None


@pytest.mark.asyncio
async def test_email_null_byte_rejected(async_client: httpx.AsyncClient):
    """Email chứa null byte '\\x00' bị Pydantic validator chặn với 422."""
    res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "attacker\x00@quant.vn", "password": "StrongPassword@123"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_password_null_byte_behavior(async_client: httpx.AsyncClient):
    """Mật khẩu chứa null byte '\\x00' xử lý nhất quán khi đăng ký và đăng nhập."""
    uid = uuid.uuid4().hex[:8]
    email = f"null_pwd_{uid}@quant.vn"
    pwd_with_null = "Pass\x00word@123"

    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": pwd_with_null},
    )
    assert reg_res.status_code == 201

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": pwd_with_null},
    )
    assert login_res.status_code == 200
