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
    weekday = now.weekday()  # 0: Thứ Hai, 4: Thứ Sáu, 5: Thứ Bảy, 6: Chủ Nhật

    # 1. Nếu là Chủ Nhật (weekday 6) -> lùi 2 ngày về Thứ Sáu
    if weekday == 6:
        target_dt = now - timedelta(days=2)
        return target_dt.strftime("%Y-%m-%d")

    # 2. Nếu là Thứ Bảy (weekday 5) -> lùi 1 ngày về Thứ Sáu
    if weekday == 5:
        target_dt = now - timedelta(days=1)
        return target_dt.strftime("%Y-%m-%d")

    # 3. Nếu là ngày trong tuần (Thứ Hai -> Thứ Sáu)
    # Kiểm tra xem đã qua 15:00 (kết thúc phiên ATC) hay chưa
    current_time = now.time()
    if current_time >= MARKET_CLOSE_TIME:
        # Đã kết thúc phiên T hôm nay
        return now.strftime("%Y-%m-%d")
    else:
        # Chưa kết thúc phiên T -> lấy phiên giao dịch liền trước
        if weekday == 0:
            # Thứ Hai trước 15:00 -> lấy Thứ Sáu tuần trước (lùi 3 ngày)
            target_dt = now - timedelta(days=3)
        else:
            # Thứ Ba đến Thứ Sáu trước 15:00 -> lấy ngày hôm qua (lùi 1 ngày)
            target_dt = now - timedelta(days=1)
        return target_dt.strftime("%Y-%m-%d")


def get_target_market_session_info(as_of: datetime | None = None) -> dict[str, Any]:
    """
    Trả về thông tin chi tiết về phiên giao dịch hiện tại phục vụ hiển thị UI và suy luận.
    """
    now = as_of or get_current_vn_time()
    weekday = now.weekday()
    target_date = get_target_market_date(now)

    is_weekend = weekday in (5, 6)
    is_after_close = (now.time() >= MARKET_CLOSE_TIME) and not is_weekend

    if is_after_close:
        session_name = "Phiên T (Đã chốt)"
        session_type = "T"
        status_label = f"Đã chốt phiên T ({now.strftime('%d/%m/%Y')})"
        prediction_horizon_desc = "Dự phóng 3 phiên tiếp theo (T+1 → T+3)"
    elif is_weekend:
        session_name = "Nghỉ cuối tuần"
        session_type = "T-1"
        status_label = f"Thị trường nghỉ • Chốt phiên Thứ Sáu ({target_date})"
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
        "is_market_closed": is_after_close or is_weekend,
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
        if curr.weekday() in (5, 6):
            continue  # Bỏ qua Thứ Bảy & Chủ Nhật

        trading_days.append({
            "day_offset": offset,
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
