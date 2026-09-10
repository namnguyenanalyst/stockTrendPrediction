"""Module thu thập, lưu trữ và làm sạch dữ liệu chứng khoán qua SSI Fast Connect Data."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from vn_stock.config import DEFAULT_START_DATE, DEFAULT_SYMBOL, RAW_DATA_DIR
from vn_stock.ssi_client import SSIFastConnectClient


def load_local_data(
    symbol: str = DEFAULT_SYMBOL,
    data_dir: Path = RAW_DATA_DIR,
) -> Optional[pd.DataFrame]:
    """Đọc dữ liệu lịch sử giá đã lưu trong thư mục data/raw/."""
    possible_names = [
        f"Cổ_phiếu_{symbol}.csv",
        f"{symbol}.csv",
        f"Cổ_phiếu_{symbol.upper()}.csv",
        f"{symbol.upper()}.csv",
    ]
    for name in possible_names:
        file_path = data_dir / name
        if file_path.exists():
            df = pd.read_csv(file_path)
            return clean_stock_data(df)
    return None


def fetch_stock_data(
    symbol: str = DEFAULT_SYMBOL,
    start_date: str = DEFAULT_START_DATE,
    end_date: Optional[str] = None,
    save_to_raw: bool = True,
    unit: str = "kVND",
) -> pd.DataFrame:
    """
    Tải dữ liệu lịch sử giá OHLCV qua SSI Fast Connect Data API.
    Nếu xảy ra lỗi kết nối hoặc chưa có API key, tự động fallback đọc dữ liệu local.
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        ssi_client = SSIFastConnectClient()
        df = ssi_client.get_daily_ohlcv(
            symbol=symbol.upper(),
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )
        if df.empty:
            raise ValueError(f"SSI không trả về dữ liệu cho mã {symbol}")
    except Exception as exc:
        # Fallback đọc dữ liệu local đã lưu từ trước nếu có lỗi mạng hoặc API
        local_df = load_local_data(symbol)
        if local_df is not None:
            return local_df
        raise RuntimeError(
            f"Không thể tải dữ liệu từ SSI FC-Data cho mã {symbol} và không tìm thấy file local: {exc}"
        ) from exc

    cleaned_df = clean_stock_data(df)

    if save_to_raw:
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        save_path = RAW_DATA_DIR / f"Cổ_phiếu_{symbol.upper()}.csv"
        cleaned_df.to_csv(save_path, index=False, encoding="utf-8-sig")

    return cleaned_df


def clean_stock_data(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hóa cột và sắp xếp dữ liệu giá theo thời gian."""
    data = df.copy()

    # Chuẩn hóa tên cột
    column_mapping = {
        "time": "Date",
        "TradingDate": "Date",
        "yyyy-mm-dd": "Date",
        "open": "Open",
        "Giá mở cửa": "Open",
        "high": "High",
        "Giá trần": "High",
        "low": "Low",
        "Giá sàn": "Low",
        "close": "Close",
        "Giá đóng cửa": "Close",
        "volume": "Volume",
        "Khối lượng giao dịch": "Volume",
    }
    for old_col, new_col in column_mapping.items():
        if old_col in data.columns and new_col not in data.columns:
            data.rename(columns={old_col: new_col}, inplace=True)

    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"])
        data = data.sort_values("Date").reset_index(drop=True)

    return data
