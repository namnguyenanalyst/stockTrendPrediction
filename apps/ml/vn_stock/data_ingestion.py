"""Module thu thập, lưu trữ Parquet và chuẩn hóa dữ liệu Long-format Panel cho rổ VN30 và VN-Index."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

from vn_stock.config import (
    DEFAULT_END_DATE,
    DEFAULT_START_DATE,
    DEFAULT_SYMBOL,
    DEFAULT_SYMBOLS,
    PANEL_DATA_DIR,
    RAW_DATA_DIR,
)
from vn_stock.ssi_client import SSIFastConnectClient


def clean_stock_data(df: pd.DataFrame, symbol: Optional[str] = None) -> pd.DataFrame:
    """Chuẩn hóa tên cột sang tiếng Anh nhất quán, sửa lỗi thuật ngữ và sắp xếp thời gian."""
    data = df.copy()

    # Chuẩn hóa tên cột (hỗ trợ cả tiếng Anh, tiếng Việt chuẩn và alias cũ)
    column_mapping = {
        "time": "Date",
        "TradingDate": "Date",
        "yyyy-mm-dd": "Date",
        "open": "Open",
        "Giá mở cửa": "Open",
        "high": "High",
        "Giá cao nhất": "High",
        "Giá trần": "High",  # Alias tương thích ngược
        "low": "Low",
        "Giá thấp nhất": "Low",
        "Giá sàn": "Low",   # Alias tương thích ngược
        "close": "Close",
        "Giá đóng cửa": "Close",
        "volume": "Volume",
        "Khối lượng": "Volume",
        "Khối lượng giao dịch": "Volume",
    }
    for old_col, new_col in column_mapping.items():
        if old_col in data.columns and new_col not in data.columns:
            data.rename(columns={old_col: new_col}, inplace=True)

    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"])
        data = data.sort_values("Date").reset_index(drop=True)

    if symbol is not None and "Symbol" not in data.columns:
        data["Symbol"] = symbol.upper()

    expected_cols = [c for c in ["Date", "Symbol", "Open", "High", "Low", "Close", "Volume"] if c in data.columns]
    other_cols = [c for c in data.columns if c not in expected_cols]
    return data[expected_cols + other_cols]


def load_local_data(
    symbol: str = DEFAULT_SYMBOL,
    data_dir: Path = RAW_DATA_DIR,
) -> Optional[pd.DataFrame]:
    """Đọc dữ liệu lịch sử giá đã lưu trong data/raw/ (ưu tiên Parquet, fallback CSV)."""
    # 1. Thử đọc Parquet
    parquet_path = data_dir / f"{symbol.upper()}.parquet"
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        return clean_stock_data(df, symbol=symbol)

    # 2. Thử đọc CSV (fallback)
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
            return clean_stock_data(df, symbol=symbol)
    return None


def fetch_daily_index(
    index_id: str = "VNINDEX",
    start_date: str = DEFAULT_START_DATE,
    end_date: Optional[str] = DEFAULT_END_DATE,
    save_to_raw: bool = True,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Tải và lưu trữ dữ liệu chỉ số thị trường (VNINDEX), tự động tính Return 1d."""
    raw_parquet_path = RAW_DATA_DIR / f"{index_id.upper()}.parquet"
    raw_csv_path = RAW_DATA_DIR / f"{index_id.upper()}.csv"

    if not force_refresh:
        if raw_parquet_path.exists():
            df = pd.read_parquet(raw_parquet_path)
            df["Date"] = pd.to_datetime(df["Date"])
            ret_col = f"{index_id.upper()}_Return_1d"
            if ret_col not in df.columns:
                df[ret_col] = df[f"{index_id.upper()}_Close"].pct_change(1)
            return df
        elif raw_csv_path.exists():
            df = pd.read_csv(raw_csv_path)
            df["Date"] = pd.to_datetime(df["Date"])
            ret_col = f"{index_id.upper()}_Return_1d"
            if ret_col not in df.columns:
                df[ret_col] = df[f"{index_id.upper()}_Close"].pct_change(1)
            return df

    # Tải mới từ API
    ssi_client = SSIFastConnectClient()
    df = ssi_client.get_daily_index(index_id=index_id, start_date=start_date, end_date=end_date)
    if df.empty:
        raise RuntimeError(f"Không thể tải dữ liệu chỉ số {index_id} từ SSI API")

    df[f"{index_id.upper()}_Return_1d"] = df[f"{index_id.upper()}_Close"].pct_change(1)

    if save_to_raw:
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(raw_parquet_path, index=False, engine="pyarrow")

    return df


def fetch_stock_data(
    symbol: str = DEFAULT_SYMBOL,
    start_date: str = DEFAULT_START_DATE,
    end_date: Optional[str] = DEFAULT_END_DATE,
    save_to_raw: bool = True,
    force_refresh: bool = False,
    unit: str = "kVND",
) -> pd.DataFrame:
    """Tải dữ liệu OHLCV đơn mã (ưu tiên đọc Parquet cache, fallback API)."""
    symbol = symbol.upper()
    if not force_refresh:
        local_df = load_local_data(symbol)
        if local_df is not None and not local_df.empty:
            return local_df

    try:
        ssi_client = SSIFastConnectClient()
        df = ssi_client.get_daily_ohlcv(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )
        if df.empty:
            raise ValueError(f"SSI không trả về dữ liệu cho mã {symbol}")
    except Exception as exc:
        local_df = load_local_data(symbol)
        if local_df is not None:
            return local_df
        raise RuntimeError(f"Lỗi thu thập dữ liệu mã {symbol}: {exc}") from exc

    cleaned_df = clean_stock_data(df, symbol=symbol)

    if save_to_raw:
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        parquet_path = RAW_DATA_DIR / f"{symbol}.parquet"
        cleaned_df.to_parquet(parquet_path, index=False, engine="pyarrow")

    return cleaned_df


def build_panel_dataset(
    symbols: Optional[Union[List[str], str]] = None,
    start_date: str = DEFAULT_START_DATE,
    end_date: Optional[str] = DEFAULT_END_DATE,
    save_to_interim: bool = True,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Thu thập dữ liệu đa mã, tích hợp chỉ số VN-Index và lưu dạng Parquet phân vùng theo Symbol.
    
    Args:
        symbols: Danh sách mã, hoặc 'VN30' để tự lấy 30 mã rổ chỉ số, hoặc None (5 mã mặc định).
        start_date: Ngày bắt đầu.
        end_date: Ngày kết thúc.
        save_to_interim: Lưu phân vùng Parquet vào data/interim/panel/.
        force_refresh: Bắt buộc tải lại từ API thay vì đọc cache.
    """
    ssi_client = SSIFastConnectClient()
    if symbols is None:
        target_symbols = DEFAULT_SYMBOLS
    elif isinstance(symbols, str) and symbols.upper() in ["VN30", "VN100"]:
        target_symbols = ssi_client.get_index_components(symbols.upper())
    elif isinstance(symbols, str):
        target_symbols = [symbols.upper()]
    else:
        target_symbols = [s.upper() for s in symbols]

    dfs: List[pd.DataFrame] = []
    for sym in target_symbols:
        try:
            df_sym = fetch_stock_data(
                symbol=sym,
                start_date=start_date,
                end_date=end_date,
                force_refresh=force_refresh,
            )
            dfs.append(df_sym)
        except Exception as e:
            print(f"⚠️ Cảnh báo: Bỏ qua mã {sym} do lỗi thu thập: {e}")

    if not dfs:
        raise RuntimeError("Không thu thập được dữ liệu cho bất kỳ mã cổ phiếu nào.")

    panel_df = pd.concat(dfs, ignore_index=True)
    panel_df = panel_df.sort_values(["Date", "Symbol"]).reset_index(drop=True)

    # Tích hợp chỉ số toàn thị trường VN-Index
    df_vnindex = fetch_daily_index(
        index_id="VNINDEX",
        start_date=start_date,
        end_date=end_date,
        force_refresh=force_refresh,
    )
    panel_df = pd.merge(
        panel_df,
        df_vnindex[["Date", "VNINDEX_Return_1d"]],
        on="Date",
        how="left",
    )

    if save_to_interim:
        PANEL_DATA_DIR.mkdir(parents=True, exist_ok=True)
        # Lưu phân vùng theo cột Symbol vào thư mục interim
        panel_df.to_parquet(
            PANEL_DATA_DIR,
            partition_cols=["Symbol"],
            engine="pyarrow",
            index=False,
        )

    return panel_df


def load_panel_dataset(
    symbols: Optional[List[str]] = None,
    panel_dir: Path = PANEL_DATA_DIR,
) -> pd.DataFrame:
    """Nạp nhanh dữ liệu Long-format từ thư mục Parquet phân vùng theo danh sách mã."""
    if not panel_dir.exists():
        raise FileNotFoundError(f"Chưa có dữ liệu panel tại {panel_dir}. Hãy gọi build_panel_dataset() trước.")

    filters = None
    if symbols is not None and len(symbols) > 0:
        clean_symbols = [s.upper() for s in symbols]
        filters = [("Symbol", "in", clean_symbols)]

    df = pd.read_parquet(panel_dir, filters=filters, engine="pyarrow")
    return df.sort_values(["Date", "Symbol"]).reset_index(drop=True)
