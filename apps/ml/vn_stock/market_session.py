"""Module quản lý phiên giao dịch thị trường chứng khoán Việt Nam (HSX/HNX).

Quy tắc vi cấu trúc thị trường:
- Giờ giao dịch: 09:00 - 11:30 (sáng) và 13:00 - 15:00 (chiều).
- Đóng cửa phiên ATC & chốt nến ngày hoàn chỉnh: 15:00 (giờ Việt Nam, UTC+7).
- Ngày giao dịch: Thứ Hai đến Thứ Sáu (không tính Thứ Bảy, Chủ Nhật và ngày nghỉ lễ).

Quy tắc xác định phiên chốt dữ liệu căn cứ:
1. Sau 15:00 các ngày làm việc (Thứ Hai - Thứ Sáu):
   Phiên T hôm nay đã hoàn tất đóng cửa -> Target date = ngày hôm nay (T).
   Dự phóng xu hướng cho 3 phiên kế tiếp: T+1 -> T+3.
2. Trước 15:00 các ngày làm việc (hoặc trong phiên):
   Phiên T chưa hoàn tất nến ngày -> Target date = ngày làm việc liền trước (T-1).
   Dự phóng xu hướng cho 3 phiên kế tiếp: T -> T+2 (hoặc T+1 -> T+3 tính từ giá mở cửa T).
3. Thứ Bảy hoặc Chủ Nhật:
   Thị trường đóng cửa -> Target date = phiên Thứ Sáu liền trước.
"""

from datetime import datetime, time as dtime, timedelta
import logging
from pathlib import Path
from typing import Any
import zoneinfo

import pandas as pd

logger = logging.getLogger(__name__)

# Múi giờ chuẩn thị trường chứng khoán Việt Nam
VN_TIMEZONE = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")

# Giờ chốt nến ngày hoàn chỉnh sau phiên ATC (15:00)
MARKET_CLOSE_TIME = dtime(15, 0, 0)


# HOSE 2026 notice, including the 25/12/2025 New Year amendment.
# https://www.hsx.vn/vi/tin-tuc/hose-thong-bao-lich-nghi-giao-dich-nam-2026/2437411
# Only this published year is verified; other years retain weekday fallback.
VERIFIED_CALENDAR_YEARS = frozenset({2026})
MARKET_HOLIDAYS = frozenset({
    "2026-01-01", "2026-01-02", "2026-02-16", "2026-02-17",
    "2026-02-18", "2026-02-19", "2026-02-20", "2026-04-27",
    "2026-04-30", "2026-05-01", "2026-08-31", "2026-09-01", "2026-09-02",
})


def is_trading_day(day: datetime) -> bool:
    return day.weekday() < 5 and day.strftime("%Y-%m-%d") not in MARKET_HOLIDAYS


def get_current_vn_time() -> datetime:
    """Lấy thời gian hiện tại theo múi giờ Việt Nam (UTC+7)."""
    try:
        return datetime.now(VN_TIMEZONE)
    except Exception:
        # Fallback nếu hệ thống không hỗ trợ zoneinfo cụ thể
        return datetime.utcnow() + timedelta(hours=7)


def get_target_market_date(as_of: datetime | None = None) -> str:
    """
    Xác định ngày của phiên giao dịch chốt gần nhất cần có trong hệ thống dữ liệu.

    Args:
        as_of: Thời điểm cần kiểm tra (mặc định là thời gian hiện tại).

    Returns:
        Chuỗi ngày định dạng 'YYYY-MM-DD'.
    """
    now = as_of or get_current_vn_time()
    # Naive caller inputs follow the documented VN-local convention;
    # aware inputs must be normalized before weekday and ATC comparisons.
    now = now.replace(tzinfo=VN_TIMEZONE) if now.tzinfo is None else now.astimezone(VN_TIMEZONE)
    target = now if now.time() >= MARKET_CLOSE_TIME else now - timedelta(days=1)
    while not is_trading_day(target):
        target -= timedelta(days=1)
    return target.strftime("%Y-%m-%d")


def get_target_market_session_info(as_of: datetime | None = None) -> dict[str, Any]:
    """
    Trả về thông tin chi tiết về phiên giao dịch hiện tại phục vụ hiển thị UI và suy luận.
    """
    now = as_of or get_current_vn_time()
    # Naive caller inputs follow the documented VN-local convention;
    # aware inputs must be normalized before weekday and ATC comparisons.
    now = now.replace(tzinfo=VN_TIMEZONE) if now.tzinfo is None else now.astimezone(VN_TIMEZONE)
    weekday = now.weekday()
    target_date = get_target_market_date(now)

    is_weekend = weekday in (5, 6)
    is_holiday = now.strftime("%Y-%m-%d") in MARKET_HOLIDAYS
    is_after_close = (now.time() >= MARKET_CLOSE_TIME) and not is_weekend and not is_holiday

    if is_after_close:
        session_name = "Phiên T (Đã chốt)"
        session_type = "T"
        status_label = f"Đã chốt phiên T ({now.strftime('%d/%m/%Y')})"
        prediction_horizon_desc = "Dự phóng 3 phiên tiếp theo (T+1 → T+3)"
    elif is_weekend or is_holiday:
        session_name = "Nghỉ lễ" if is_holiday else "Nghỉ cuối tuần"
        session_type = "T-1"
        status_label = f"Thị trường nghỉ • Căn cứ phiên chốt ({target_date})"
        prediction_horizon_desc = "Dự phóng 3 phiên tuần tới (T+1 → T+3)"
    else:
        session_name = "Đang trong phiên T"
        session_type = "T-1"
        status_label = f"Đang giao dịch phiên T • Căn cứ phiên T-1 ({target_date})"
        prediction_horizon_desc = "Dự phóng 3 phiên từ giá mở cửa T (T → T+2)"

    return {
        "current_time": now.strftime("%H:%M:%S %d/%m/%Y"),
        "current_date": now.strftime("%Y-%m-%d"),
        "target_date": target_date,
        "session_type": session_type,
        "session_name": session_name,
        "status_label": status_label,
        "is_market_closed": is_after_close or is_weekend or is_holiday,
        "is_holiday": is_holiday,
        "holiday_calendar_verified": now.year in VERIFIED_CALENDAR_YEARS,
        "is_weekend": is_weekend,
        "prediction_horizon_desc": prediction_horizon_desc,
    }


def get_future_trading_days(base_date: str, count: int = 3) -> list[dict[str, Any]]:
    """
    Tính toán danh sách các ngày giao dịch tương lai (bỏ qua Thứ Bảy, Chủ Nhật).

    Args:
        base_date: Ngày chốt căn cứ (YYYY-MM-DD).
        count: Số phiên tương lai cần tính (mặc định 3 phiên: T+1, T+2, T+3).

    Returns:
        Danh sách dict chứa day_offset, day_name ('T+1', 'T+2', 'T+3'), date, formatted_date.
    """
    dt = datetime.strptime(base_date, "%Y-%m-%d")
    trading_days = []
    curr = dt
    offset = 1

    while len(trading_days) < count:
        curr += timedelta(days=1)
        if not is_trading_day(curr):
            continue  # Bỏ qua Thứ Bảy & Chủ Nhật

        trading_days.append({
            "day_offset": offset,
            "holiday_calendar_verified": curr.year in VERIFIED_CALENDAR_YEARS,
            "day_name": f"T+{offset}",
            "date": curr.strftime("%Y-%m-%d"),
            "formatted_date": curr.strftime("%d/%m/%Y"),
        })
        offset += 1

    return trading_days


def check_symbol_cache_is_up_to_date(
    symbol: str,
    raw_data_dir: Path,
    target_date: str | None = None,
) -> bool:
    """
    Kiểm tra xem file Parquet của một mã đã chứa dữ liệu tới target_date hay chưa.
    """
    target = target_date or get_target_market_date()
    target_dt = pd.to_datetime(target)

    # 1. Kiểm tra raw parquet
    parquet_path = raw_data_dir / f"{symbol.upper()}.parquet"
    if not parquet_path.exists():
        return False

    try:
        df = pd.read_parquet(parquet_path, columns=["Date"])
        if df.empty or "Date" not in df.columns:
            return False
        max_date = pd.to_datetime(df["Date"]).max()
        return max_date >= target_dt
    except Exception as exc:
        logger.warning("Lỗi đọc cache kiểm tra ngày cho %s: %s", symbol, exc)
        return False
