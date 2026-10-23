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
