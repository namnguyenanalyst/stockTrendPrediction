#!/usr/bin/env python3
"""Autonomous Retrain Worker Service (Option A: Dedicated Service).

Định kỳ kích hoạt huấn luyện lại mô hình học máy (LightGBM & PyTorch LSTM)
cho toàn bộ danh mục VN30 vào 02:00 Chủ Nhật hàng tuần (Giờ Việt Nam UTC+7).

Giao tiếp với FastAPI Backend thông qua endpoint nội bộ bảo vệ bởi X-Internal-Worker-Secret:
POST http://vn_stock_api:8000/api/v1/predict/retrain
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib import error, request

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [RetrainWorker] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("retrain_worker")

# Múi giờ Việt Nam UTC+7
ICT = timezone(timedelta(hours=7))


def get_current_ict_time() -> datetime:
    """Lấy thời gian hiện tại theo múi giờ Việt Nam (UTC+7)."""
    return datetime.now(timezone.utc).astimezone(ICT)


def trigger_retrain(
    api_base_url: str,
    secret: str | None,
    scope: str = "VN30",
    horizon: int = 3,
    threshold: float = 0.02,
    val_buffer_days: int = 40,
    timeout: int = 600,
) -> dict:
    """Gửi HTTP POST yêu cầu FastAPI Backend huấn luyện lại mô hình sản xuất."""
    if not secret:
        raise ValueError("INTERNAL_WORKER_SECRET không được để trống hoặc None.")

    endpoint = f"{api_base_url.rstrip('/')}/api/v1/predict/retrain"
    payload = {
        "horizon": horizon,
        "threshold": threshold,
        "val_buffer_days": val_buffer_days,
        "scope": scope,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-Internal-Worker-Secret": secret,
        "User-Agent": "VNStock-Autonomous-Retrain-Worker/1.0",
    }

    req = request.Request(endpoint, data=data, headers=headers, method="POST")
    logger.info("Bắt đầu kích hoạt huấn luyện lại mô hình tại: %s (scope=%s)", endpoint, scope)
    start_time = time.time()

    try:
        with request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            raw_body = response.read().decode("utf-8")
            result = json.loads(raw_body)
            elapsed = time.time() - start_time
            logger.info(
                "Huấn luyện lại hoàn tất thành công [HTTP %d] trong %.2f giây: %s",
                status_code,
                elapsed,
                result.get("message", "OK"),
            )
            return result
    except error.HTTPError as http_err:
        err_msg = http_err.read().decode("utf-8") if http_err.fp else str(http_err)
        logger.error("API trả về lỗi HTTP %d: %s", http_err.code, err_msg)
        raise RuntimeError(f"HTTP Error {http_err.code}: {err_msg}") from http_err
    except error.URLError as url_err:
        logger.error("Không thể kết nối tới API server tại %s: %s", endpoint, url_err.reason)
        raise RuntimeError(f"Connection Error: {url_err.reason}") from url_err


def is_scheduled_time(
    current_dt: datetime,
    last_run_date: str | None,
    target_weekday: int = 6,  # 6 = Sunday (Monday=0)
    target_hour: int = 2,     # 02:00 ICT
    target_minute: int = 0,
    window_minutes: int = 15,
) -> bool:
    """Xác định thời điểm hiện tại có nằm trong cửa sổ kích hoạt Chủ Nhật 02:00 ICT hay không."""
    today_str = current_dt.strftime("%Y-%m-%d")
    if last_run_date == today_str:
        return False

    if current_dt.weekday() != target_weekday:
        return False

    return current_dt.hour == target_hour and (
        target_minute <= current_dt.minute < target_minute + window_minutes
    )


def run_worker_loop(
    api_base_url: str,
    secret: str | None,
    scope: str = "VN30",
    check_interval: int = 30,
    target_weekday: int = 6,
    target_hour: int = 2,
    target_minute: int = 0,
) -> None:
    """Vòng lặp tiến trình giám sát và chạy cron retrain định kỳ."""
    logger.info("Khởi động Autonomous Retrain Worker (Phương án A: Docker Container riêng)")
    logger.info("API URL: %s", api_base_url)
    logger.info(
        "Lịch định kỳ: Thứ %s lúc %02d:%02d (Giờ Việt Nam UTC+7)",
        "Chủ Nhật" if target_weekday == 6 else f"{target_weekday + 1}",
        target_hour,
        target_minute,
    )

    last_run_date: str | None = None

    while True:
        try:
            now_ict = get_current_ict_time()
            if is_scheduled_time(
                current_dt=now_ict,
                last_run_date=last_run_date,
                target_weekday=target_weekday,
                target_hour=target_hour,
                target_minute=target_minute,
            ):
                logger.info("Phát hiện lịch hẹn Chủ Nhật 02:00 ICT. Kích hoạt retrain worker...")
                try:
                    trigger_retrain(
                        api_base_url=api_base_url,
                        secret=secret,
                        scope=scope,
                    )
                    last_run_date = now_ict.strftime("%Y-%m-%d")
                    logger.info("Đã đánh dấu hoàn tất phiên huấn luyện ngày %s", last_run_date)
                except (RuntimeError, ValueError, OSError, TimeoutError, error.URLError, error.HTTPError) as exc:
                    logger.error("Lỗi thực thi retrain trong lịch hẹn: %s", exc)
        except (RuntimeError, ValueError, OSError, TimeoutError) as loop_err:
            logger.error("Lỗi trong vòng lặp worker: %s", loop_err)

        time.sleep(check_interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Autonomous Retrain Worker for VN Stock")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Chạy 1 lần duy nhất rồi thoát (phục vụ test hoặc manual trigger)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=os.getenv("API_BASE_URL", "http://vn_stock_api:8000"),
        help="Base URL của Backend API",
    )
    parser.add_argument(
        "--scope",
        type=str,
        default=os.getenv("RETRAIN_SCOPE", "VN30"),
        help="Phạm vi huấn luyện (mặc định: VN30)",
    )
    args = parser.parse_args()

    secret = os.getenv("INTERNAL_WORKER_SECRET")
    if not secret:
        logger.warning(
            "CẢNH BÁO: INTERNAL_WORKER_SECRET chưa được thiết lập. Worker sẽ thất bại khi gửi request xác thực."
        )

    if args.once or os.getenv("RUN_ONCE", "").lower() in ("true", "1"):
        logger.info("Chế độ chạy 1 lần (--once)...")
        trigger_retrain(api_base_url=args.api_url, secret=secret, scope=args.scope)
        sys.exit(0)

    run_worker_loop(
        api_base_url=args.api_url,
        secret=secret,
        scope=args.scope,
    )


if __name__ == "__main__":
    main()
