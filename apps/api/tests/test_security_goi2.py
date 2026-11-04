"""Bộ kiểm thử Bảo mật Backend, Phân quyền PoLP và Thống kê Quản trị (Gói 2).

Bao gồm 11 nhóm kiểm thử bảo mật nghiêm ngặt:
1. `test_retrain_no_secret_returns_403`: Gọi retrain thiếu secret header -> 403 Forbidden.
2. `test_retrain_wrong_secret_returns_403`: Gọi retrain sai secret header -> 403 Forbidden.
3. `test_retrain_unset_secret_fail_closed`: Khi secret chưa cấu hình -> fail-closed 403 Forbidden.
4. `test_retrain_valid_secret_success`: Khi secret header khớp -> thành công 200 OK.
5. `test_polp_admin_cannot_access_other_users_watchlist`: Token Admin truy cập/xóa watchlist người khác -> 404 Not Found.
6. `test_polp_admin_cannot_access_other_users_preset`: Token Admin truy cập/xóa preset người khác -> 404 Not Found.
7. `test_polp_admin_cannot_delete_other_users_backtest`: Token Admin xóa backtest người khác -> 404 Not Found.
8. `test_admin_stats_forbidden_for_trader`: TRADER gọi GET /api/v1/admin/stats -> 403 Forbidden.
9. `test_admin_stats_unauthorized_for_anonymous`: Nặc danh gọi GET /api/v1/admin/stats -> 401 Unauthorized.
10. `test_admin_stats_utc7_midnight_boundary_and_online`: Xác minh 5 trường thống kê và ranh giới 0h00 UTC+7.
11. `test_predict_status_endpoint`: Kiểm tra GET /api/v1/predict/status trả đúng 2 trường và last_retrain_at null.
"""

import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.models.user import User, UserRole

VN_TZ = timezone(timedelta(hours=7))


async def _create_test_user(
    session: AsyncSession,
    email: str,
    role: UserRole = UserRole.TRADER,
    created_at: datetime | None = None,
    last_seen_at: datetime | None = None,
) -> tuple[User, str]:
    """Helper tạo user trong test DB và sinh access token."""
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=get_password_hash("StrongSecret@123"),
        role=role,
        is_active=True,
    )
    if created_at is not None:
        user.created_at = created_at
    if last_seen_at is not None:
        user.last_seen_at = last_seen_at

    session.add(user)
    await session.commit()
    await session.refresh(user)
    token = create_access_token(subject=user.id, extra_claims={"role": role.value})
    return user, token


# =============================================================================
# 1. Bảo vệ Endpoint Retrain (/retrain)
# =============================================================================


@pytest.mark.asyncio
async def test_retrain_no_secret_returns_403(async_client: httpx.AsyncClient):
    """Gọi POST /api/v1/predict/retrain không có header X-Internal-Worker-Secret phải trả 403."""
    with patch.object(settings, "INTERNAL_WORKER_SECRET", "super_worker_secret_key"):
        res = await async_client.post("/api/v1/predict/retrain", json={"horizon": 3})
        assert res.status_code == 403
        assert "Invalid or missing internal worker secret" in res.json()["detail"]


@pytest.mark.asyncio
async def test_retrain_wrong_secret_returns_403(async_client: httpx.AsyncClient):
    """Gọi POST /api/v1/predict/retrain với sai secret phải trả 403."""
    with patch.object(settings, "INTERNAL_WORKER_SECRET", "super_worker_secret_key"):
        res = await async_client.post(
            "/api/v1/predict/retrain",
            json={"horizon": 3},
            headers={"X-Internal-Worker-Secret": "wrong_attacker_secret"},
        )
        assert res.status_code == 403
        assert "Invalid or missing internal worker secret" in res.json()["detail"]


@pytest.mark.asyncio
async def test_retrain_unset_secret_fail_closed(async_client: httpx.AsyncClient):
    """Khi INTERNAL_WORKER_SECRET chưa đặt (None hoặc rỗng), hệ thống phải fail-closed trả 403."""
    with patch.object(settings, "INTERNAL_WORKER_SECRET", None):
        res = await async_client.post(
            "/api/v1/predict/retrain",
            json={"horizon": 3},
            headers={"X-Internal-Worker-Secret": "any_secret"},
        )
        assert res.status_code == 403

    with patch.object(settings, "INTERNAL_WORKER_SECRET", ""):
        res2 = await async_client.post(
            "/api/v1/predict/retrain",
            json={"horizon": 3},
            headers={"X-Internal-Worker-Secret": ""},
        )
        assert res2.status_code == 403


@pytest.mark.asyncio
async def test_retrain_valid_secret_success(async_client: httpx.AsyncClient):
    """Khi header X-Internal-Worker-Secret khớp hoàn toàn, retrain được thực thi và trả 200."""
    secret = "verified_worker_secret_production_2026"
    mock_ret = {
        "status": "success",
        "horizon": "T+3",
        "lightgbm_metrics": {"accuracy": 0.68},
        "lstm_metrics": {"accuracy": 0.64},
    }
    with patch.object(settings, "INTERNAL_WORKER_SECRET", secret), \
         patch("vn_stock.modeling.train.train_production_model", return_value=mock_ret):
        res = await async_client.post(
            "/api/v1/predict/retrain",
            json={"horizon": 3, "threshold": 0.02, "val_buffer_days": 40, "scope": "VN30"},
            headers={"X-Internal-Worker-Secret": secret},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["horizon"] == "T+3"


# =============================================================================
# 2. Nguyên tắc Đặc quyền Tối thiểu (PoLP): Admin không được truy cập/xóa tài nguyên user khác
# =============================================================================


@pytest.mark.asyncio
async def test_polp_admin_cannot_access_other_users_watchlist(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    """Admin không được quyền xem hoặc xóa Watchlist của người dùng khác (phải nhận 404 Not Found)."""
    # 1. Tạo User thông thường và tạo Watchlist
    _trader, trader_token = await _create_test_user(db_session, "trader_wl@quant.vn", UserRole.TRADER)
    trader_headers = {"Authorization": f"Bearer {trader_token}"}
    create_res = await async_client.post(
        "/api/v1/user/watchlists",
        json={"name": "Trader Watchlist", "symbols": ["VIC", "HPG"]},
        headers=trader_headers,
    )
    assert create_res.status_code == 201
    watchlist_id = create_res.json()["id"]

    # 2. Tạo Admin
    _admin, admin_token = await _create_test_user(db_session, "admin_wl@quant.vn", UserRole.ADMIN)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Admin cố gắng xóa Watchlist của trader -> Phải trả về 404 Not Found
    del_res = await async_client.delete(
        f"/api/v1/user/watchlists/{watchlist_id}",
        headers=admin_headers,
    )
    assert del_res.status_code == 404
    assert del_res.json()["detail"] == "Watchlist not found"

    # 4. Admin lấy danh sách watchlist -> Không nhìn thấy watchlist của trader
    list_res = await async_client.get("/api/v1/user/watchlists", headers=admin_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0


@pytest.mark.asyncio
async def test_polp_admin_cannot_access_other_users_preset(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    """Admin không được quyền xem hoặc xóa Strategy Preset của người dùng khác (phải nhận 404 Not Found)."""
    # 1. Tạo User thông thường và tạo Preset
    _trader, trader_token = await _create_test_user(db_session, "trader_pre@quant.vn", UserRole.TRADER)
    trader_headers = {"Authorization": f"Bearer {trader_token}"}
    create_res = await async_client.post(
        "/api/v1/user/presets",
        json={"name": "Trader Preset", "description": "Desc", "parameters": {"stop_loss": 0.05}},
        headers=trader_headers,
    )
    assert create_res.status_code == 201
    preset_id = create_res.json()["id"]

    # 2. Tạo Admin
    _admin, admin_token = await _create_test_user(db_session, "admin_pre@quant.vn", UserRole.ADMIN)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Admin cố gắng xóa Preset của trader -> Phải trả về 404 Not Found
    del_res = await async_client.delete(
        f"/api/v1/user/presets/{preset_id}",
        headers=admin_headers,
    )
    assert del_res.status_code == 404
    assert del_res.json()["detail"] == "Strategy preset not found"

    # 4. Admin lấy danh sách presets -> Không nhìn thấy preset của trader
    list_res = await async_client.get("/api/v1/user/presets", headers=admin_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0


@pytest.mark.asyncio
async def test_polp_admin_cannot_delete_other_users_backtest(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    """Admin không được quyền xem hoặc xóa Backtest History của người dùng khác (phải nhận 404 Not Found)."""
    # 1. Tạo User thông thường và lưu Backtest
    _trader, trader_token = await _create_test_user(db_session, "trader_bt@quant.vn", UserRole.TRADER)
    trader_headers = {"Authorization": f"Bearer {trader_token}"}
    create_res = await async_client.post(
        "/api/v1/user/backtests",
        json={
            "symbol": "FPT",
            "strategy_name": "AI Momentum",
            "strategy_type": "ml_enhanced",
            "start_date": "2024-01-01",
            "end_date": "2024-04-01",
            "initial_capital": 100000000.0,
            "total_return": 0.15,
            "sharpe_ratio": 1.45,
            "max_drawdown": 0.08,
            "win_rate": 0.65,
            "equity_curve": [{"date": "2024-01-01", "equity": 100000000.0}],
        },
        headers=trader_headers,
    )
    assert create_res.status_code == 201
    backtest_id = create_res.json()["id"]

    # 2. Tạo Admin
    _admin, admin_token = await _create_test_user(db_session, "admin_bt@quant.vn", UserRole.ADMIN)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Admin cố gắng xóa Backtest của trader -> Phải trả về 404 Not Found
    del_res = await async_client.delete(
        f"/api/v1/user/backtests/{backtest_id}",
        headers=admin_headers,
    )
    assert del_res.status_code == 404
    assert del_res.json()["detail"] == "Backtest not found"

    # 4. Admin lấy danh sách backtests -> Không nhìn thấy backtest của trader
    list_res = await async_client.get("/api/v1/user/backtests", headers=admin_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0


# =============================================================================
# 3. Phân quyền và Xác thực Thống kê Quản trị (Admin Stats)
# =============================================================================


@pytest.mark.asyncio
async def test_admin_stats_forbidden_for_trader(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    """TRADER gọi GET /api/v1/admin/stats bị từ chối với HTTP 403 Forbidden."""
    _, trader_token = await _create_test_user(db_session, "trader_stats@quant.vn", UserRole.TRADER)
    res = await async_client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {trader_token}"},
    )
    assert res.status_code == 403
    assert "Admin role required" in res.json()["detail"]


@pytest.mark.asyncio
async def test_admin_stats_unauthorized_for_anonymous(async_client: httpx.AsyncClient):
    """Request nặc danh gọi GET /api/v1/admin/stats bị từ chối với HTTP 401 Unauthorized."""
    res = await async_client.get("/api/v1/admin/stats")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_stats_utc7_midnight_boundary_and_online(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    """Xác minh chính xác 5 chỉ số thống kê admin và ranh giới 0h00 UTC+7."""
    now_utc = datetime.now(timezone.utc)
    now_vn = now_utc.astimezone(VN_TZ)
    today_midnight_vn = now_vn.replace(hour=0, minute=0, second=0, microsecond=0)

    # Các mốc thời gian kiểm thử:
    # 1. 23:30 ICT hôm qua (16:30 UTC hôm qua) -> Trước 0h00 ICT -> KHÔNG thuộc today, THUỘC 7d, 30d, total
    yesterday_2330_utc = (today_midnight_vn - timedelta(minutes=30)).astimezone(timezone.utc)
    # 2. 00:30 ICT hôm nay (17:30 UTC hôm qua) -> Sau 0h00 ICT -> THUỘC today, 7d, 30d, total
    today_0030_utc = (today_midnight_vn + timedelta(minutes=30)).astimezone(timezone.utc)
    # 3. 3 ngày trước ICT -> KHÔNG thuộc today, THUỘC 7d, 30d, total
    three_days_ago_utc = (today_midnight_vn - timedelta(days=3)).astimezone(timezone.utc)
    # 4. 15 ngày trước ICT -> KHÔNG thuộc today, KHÔNG thuộc 7d, THUỘC 30d, total
    fifteen_days_ago_utc = (today_midnight_vn - timedelta(days=15)).astimezone(timezone.utc)
    # 5. 45 ngày trước ICT -> KHÔNG thuộc today, KHÔNG thuộc 7d, KHÔNG thuộc 30d, THUỘC total
    forty_five_days_ago_utc = (today_midnight_vn - timedelta(days=45)).astimezone(timezone.utc)

    # Tạo các user giả định
    _u1, _ = await _create_test_user(
        db_session, "u_2330@test.vn", UserRole.TRADER,
        created_at=yesterday_2330_utc,
        last_seen_at=now_utc - timedelta(minutes=2),  # Online (2 min ago)
    )
    _u2, _ = await _create_test_user(
        db_session, "u_0030@test.vn", UserRole.TRADER,
        created_at=today_0030_utc,
        last_seen_at=now_utc - timedelta(minutes=10), # Offline (10 min ago)
    )
    _u3, _ = await _create_test_user(
        db_session, "u_3d@test.vn", UserRole.TRADER,
        created_at=three_days_ago_utc,
        last_seen_at=None,                            # Offline (None)
    )
    _u4, _ = await _create_test_user(
        db_session, "u_15d@test.vn", UserRole.TRADER,
        created_at=fifteen_days_ago_utc,
        last_seen_at=now_utc - timedelta(minutes=20), # Offline
    )
    _u5, _ = await _create_test_user(
        db_session, "u_45d@test.vn", UserRole.TRADER,
        created_at=forty_five_days_ago_utc,
        last_seen_at=None,                            # Offline
    )

    # Admin user (tạo lúc này, online)
    _admin, admin_token = await _create_test_user(
        db_session, "admin_stats_master@test.vn", UserRole.ADMIN,
        created_at=now_utc,
        last_seen_at=now_utc,
    )

    # Admin gọi API thống kê
    res = await async_client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()

    # Xác minh đúng duy nhất 5 trường
    expected_fields = {"total_users", "new_users_today", "new_users_7d", "new_users_30d", "online_users"}
    assert set(data.keys()) == expected_fields

    # Tuyệt đối không rò rỉ thông tin cá nhân
    assert "email" not in data
    assert "users" not in data
    assert "names" not in data

    # Kiểm tra số lượng chính xác:
    # Tổng: 5 trader + 1 admin = 6
    assert data["total_users"] == 6
    # Hôm nay (>= 0h00 ICT): u2 (00:30 ICT) + admin (now) = 2 (u1 đăng ký lúc 23:30 ICT hôm trước KHÔNG ĐƯỢC TÍNH)
    assert data["new_users_today"] == 2
    # 7 ngày qua: u1, u2, u3, admin = 4
    assert data["new_users_7d"] == 4
    # 30 ngày qua: u1, u2, u3, u4, admin = 5
    assert data["new_users_30d"] == 5
    # Online (last_seen_at >= now - 5 min): u1 (2m ago) + admin (now) = 2
    assert data["online_users"] == 2


# =============================================================================
# 4. Endpoint Trạng thái Mô hình (/predict/status)
# =============================================================================


@pytest.mark.asyncio
async def test_predict_status_endpoint(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    tmp_path,
):
    """Kiểm tra GET /api/v1/predict/status trả đúng 2 trường, null khi chưa retrain và timestamp khi đã retrain."""
    # 1. Yêu cầu đăng nhập: nặc danh bị từ chối 401
    anon_res = await async_client.get("/api/v1/predict/status")
    assert anon_res.status_code == 401

    # 2. Đăng nhập với TRADER (mọi role đều có quyền xem status)
    _, token = await _create_test_user(db_session, "trader_status@quant.vn", UserRole.TRADER)
    headers = {"Authorization": f"Bearer {token}"}

    # Trường hợp 1: File production_training_info_t3.json chưa tồn tại (chưa từng retrain)
    empty_models_dir = tmp_path / "models_empty"
    empty_models_dir.mkdir(parents=True, exist_ok=True)
    with patch.object(settings, "MODELS_DIR", empty_models_dir):
        res1 = await async_client.get("/api/v1/predict/status", headers=headers)
        assert res1.status_code == 200
        data1 = res1.json()
        assert set(data1.keys()) == {"last_atc_session_date", "last_retrain_at"}
        assert isinstance(data1["last_atc_session_date"], str)
        assert len(data1["last_atc_session_date"]) == 10  # YYYY-MM-DD
        assert data1["last_retrain_at"] is None

    # Trường hợp 2: File production_training_info_t3.json đã có timestamp
    info_dir = tmp_path / "models_with_info"
    info_dir.mkdir(parents=True, exist_ok=True)
    sample_timestamp = "2026-11-04 15:30:00"
    (info_dir / "production_training_info_t3.json").write_text(
        json.dumps({"timestamp": sample_timestamp, "scope": "VN30"}),
        encoding="utf-8",
    )
    with patch.object(settings, "MODELS_DIR", info_dir):
        res2 = await async_client.get("/api/v1/predict/status", headers=headers)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["last_retrain_at"] == sample_timestamp
