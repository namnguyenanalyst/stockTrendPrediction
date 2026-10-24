"""Kiểm thử tự động cho module market_session và cơ chế đồng bộ nến thị trường phiên T/T-1."""

from datetime import datetime, time as dtime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from vn_stock.market_session import (
    MARKET_CLOSE_TIME,
    check_symbol_cache_is_up_to_date,
    get_future_trading_days,
    get_target_market_date,
    get_target_market_session_info,
)


def test_target_market_date_after_15_pm():
    """Sau 15:00 ngày trong tuần (Thứ Hai -> Thứ Sáu) mục tiêu là phiên T ngày hôm nay."""
    # Thứ Năm 2026-10-22 lúc 15:30 (sau ATC)
    dt_thursday_after = datetime(2026, 10, 22, 15, 30, 0)
    target = get_target_market_date(dt_thursday_after)
    assert target == "2026-10-22"


def test_target_market_date_before_15_pm():
    """Trước 15:00 ngày trong tuần mục tiêu là phiên T-1 liền trước."""
    # Thứ Năm 2026-10-22 lúc 10:15 (đang giao dịch phiên sáng)
    dt_thursday_morning = datetime(2026, 10, 22, 10, 15, 0)
    target = get_target_market_date(dt_thursday_morning)
    assert target == "2026-10-21"

    # Thứ Hai 2026-10-26 lúc 09:30 -> mục tiêu là Thứ Sáu tuần trước (2026-10-23)
    dt_monday_morning = datetime(2026, 10, 26, 9, 30, 0)
    target_monday = get_target_market_date(dt_monday_morning)
    assert target_monday == "2026-10-23"


def test_target_market_date_weekend():
    """Ngày cuối tuần (Thứ Bảy, Chủ Nhật) mục tiêu là phiên Thứ Sáu gần nhất."""
    # Thứ Bảy 2026-10-24
    dt_sat = datetime(2026, 10, 24, 14, 0, 0)
    assert get_target_market_date(dt_sat) == "2026-10-23"

    # Chủ Nhật 2026-10-25
    dt_sun = datetime(2026, 10, 25, 20, 0, 0)
    assert get_target_market_date(dt_sun) == "2026-10-23"


def test_get_target_market_session_info():
    """Kiểm tra cấu trúc và tính đầy đủ của session info."""
    info = get_target_market_session_info()
    assert "target_date" in info
    assert "session_type" in info
    assert "session_name" in info
    assert "status_label" in info
    assert "prediction_horizon_desc" in info
    assert info["session_type"] in ["T", "T-1"]


def test_get_future_trading_days():
    """Kiểm tra tính toán ngày giao dịch tương lai bỏ qua Thứ Bảy và Chủ Nhật."""
    # Ngày căn cứ Thứ Năm 2026-10-22
    # T+1: Thứ Sáu 2026-10-23
    # T+2: Thứ Hai 2026-10-26 (bỏ qua 24, 25)
    # T+3: Thứ Ba 2026-10-27
    days = get_future_trading_days("2026-10-22", count=3)
    assert len(days) == 3
    assert days[0]["day_name"] == "T+1"
    assert days[0]["date"] == "2026-10-23"

    assert days[1]["day_name"] == "T+2"
    assert days[1]["date"] == "2026-10-26"

    assert days[2]["day_name"] == "T+3"
    assert days[2]["date"] == "2026-10-27"


def test_check_symbol_cache_is_up_to_date(tmp_path):
    """Kiểm tra hàm đánh giá tính tươi mới của file cache."""
    # 1. File chưa tồn tại -> False
    assert not check_symbol_cache_is_up_to_date("VIC", tmp_path, target_date="2026-10-22")

    # 2. File chỉ có nến đến 2026-10-21 -> False
    df_old = pd.DataFrame({"Date": pd.to_datetime(["2026-10-20", "2026-10-21"])})
    df_old.to_parquet(tmp_path / "VIC.parquet")
    assert not check_symbol_cache_is_up_to_date("VIC", tmp_path, target_date="2026-10-22")

    # 3. File đã cập nhật đến 2026-10-22 -> True
    df_new = pd.DataFrame({"Date": pd.to_datetime(["2026-10-21", "2026-10-22"])})
    df_new.to_parquet(tmp_path / "VIC.parquet")
    assert check_symbol_cache_is_up_to_date("VIC", tmp_path, target_date="2026-10-22")

    # 4. File rỗng hoặc không có cột Date -> False
    df_no_date = pd.DataFrame({"Price": [10.0, 20.0]})
    df_no_date.to_parquet(tmp_path / "HPG.parquet")
    assert not check_symbol_cache_is_up_to_date("HPG", tmp_path, target_date="2026-10-22")

    # 5. File hỏng/corrupted binary -> False (không văng crash ngoại lệ)
    corrupted_file = tmp_path / "VNM.parquet"
    corrupted_file.write_bytes(b"not a valid parquet file content")
    assert not check_symbol_cache_is_up_to_date("VNM", tmp_path, target_date="2026-10-22")


def test_market_session_info_states():
    """Kiểm tra các trạng thái chi tiết của phiên giao dịch: sau 15h, trong phiên, cuối tuần."""
    # 1. Sau 15:00 ngày thường
    dt_after = datetime(2026, 10, 22, 16, 0, 0)
    info_after = get_target_market_session_info(dt_after)
    assert info_after["session_type"] == "T"
    assert info_after["is_market_closed"] is True
    assert "Đã chốt phiên T" in info_after["status_label"]
    assert "T+1 → T+3" in info_after["prediction_horizon_desc"]

    # 2. Đang trong phiên giao dịch (10:30 sáng Thứ Tư)
    dt_mid = datetime(2026, 10, 21, 10, 30, 0)
    info_mid = get_target_market_session_info(dt_mid)
    assert info_mid["session_type"] == "T-1"
    assert info_mid["is_market_closed"] is False
    assert info_mid["is_weekend"] is False
    assert "Đang giao dịch phiên T" in info_mid["status_label"]

    # 3. Nghỉ cuối tuần (Thứ Bảy)
    dt_sat = datetime(2026, 10, 24, 11, 0, 0)
    info_sat = get_target_market_session_info(dt_sat)
    assert info_sat["session_type"] == "T-1"
    assert info_sat["is_market_closed"] is True
    assert info_sat["is_weekend"] is True
    assert "Nghỉ cuối tuần" in info_sat["session_name"]


def test_get_current_vn_time_fallback():
    """Kiểm tra cơ chế fallback khi hệ thống gặp lỗi zoneinfo."""
    from vn_stock.market_session import get_current_vn_time

    with patch("datetime.datetime") as mock_dt:
        mock_dt.now.side_effect = Exception("ZoneInfo lookup error")
        mock_dt.utcnow.return_value = datetime(2026, 10, 24, 12, 0, 0)
        res = get_current_vn_time()
        assert res is not None

