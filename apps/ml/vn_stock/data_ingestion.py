import logging
from pathlib import Path
import shutil
import time
from typing import Any

import pandas as pd

from vn_stock.config import (
    DEFAULT_END_DATE,
    DEFAULT_START_DATE,
    DEFAULT_SYMBOL,
    DEFAULT_SYMBOLS,
    PANEL_DATA_DIR,
    RAW_DATA_DIR,
    VN30_SYMBOLS,
    get_default_end_date,
)
from vn_stock.market_session import (
    get_target_market_date,
    get_target_market_session_info,
)
from vn_stock.ssi_client import SSIFastConnectClient

logger = logging.getLogger(__name__)


class InsufficientDataCoverageError(ValueError):
    """Ngoại lệ khi dữ liệu của một mã không bao phủ đủ dải ngày yêu cầu trong panel."""


def validate_downloaded_data(
    df: pd.DataFrame,
    expected_start: str,
    expected_end: str | None = None,
    is_index: bool = False,
    symbol_name: str = "",
) -> None:
    """Kiểm tra tính toàn vẹn 5 điều kiện hợp lệ trước khi ghi nguyên tử ra đĩa."""
    if df.empty:
        raise ValueError(f"Dữ liệu tải về của {symbol_name} rỗng.")

    if "Date" not in df.columns:
        raise ValueError(f"Dữ liệu của {symbol_name} thiếu cột 'Date'.")

    # 1. Date không trùng lặp và tăng dần đơn điệu
    dup_dates = df["Date"].duplicated().sum()
    if dup_dates > 0:
        raise ValueError(f"Dữ liệu {symbol_name} có {dup_dates} ngày bị trùng lặp.")
    if not df["Date"].is_monotonic_increasing:
        raise ValueError(f"Cột 'Date' của {symbol_name} chưa được sắp xếp tăng dần đơn điệu.")

    # 2. High >= Low và Close > 0
    if not is_index:
        if "High" in df.columns and "Low" in df.columns:
            invalid_hl = (df["High"] < df["Low"]).sum()
            if invalid_hl > 0:
                raise ValueError(
                    f"Dữ liệu {symbol_name} có {invalid_hl} phiên High < Low bất thường."
                )
        if "Close" in df.columns and (df["Close"] <= 0).any():
            raise ValueError(f"Dữ liệu {symbol_name} có phiên Close <= 0.")
        if "Volume" in df.columns:
            zero_vol = (df["Volume"] == 0).sum()
            if zero_vol > 0:
                logger.warning("Mã %s có %d phiên có Volume = 0.", symbol_name, zero_vol)
    else:
        close_col = [c for c in df.columns if "Close" in c]
        if close_col and (df[close_col[0]] <= 0).any():
            raise ValueError(f"Dữ liệu chỉ số {symbol_name} có phiên Close <= 0.")

    # 3. Phủ đúng khoảng ngày yêu cầu
    min_date = df["Date"].min()
    max_date = df["Date"].max()
    target_start = pd.to_datetime(expected_start)

    if min_date > target_start + pd.Timedelta(days=4):
        raise ValueError(
            f"Dữ liệu {symbol_name} không phủ đủ ngày bắt đầu: min_date={min_date.strftime('%Y-%m-%d')} "
            f"> expected_start={expected_start}."
        )
    elif min_date > target_start:
        logger.info(
            "Mã %s: Ngày đầu (%s) khớp start_date (%s) sau dung sai ngày nghỉ lễ/cuối tuần.",
            symbol_name,
            min_date.strftime("%Y-%m-%d"),
            expected_start,
        )

    if expected_end is not None:
        target_end = pd.to_datetime(expected_end)
        # Dung sai 4 ngày cho ngày nghỉ lễ hoặc cuối tuần nếu expected_end rơi vào ngày không giao dịch
        if max_date < target_end - pd.Timedelta(days=4):
            raise ValueError(
                f"Dữ liệu {symbol_name} không phủ đủ ngày kết thúc cố định: max_date={max_date.strftime('%Y-%m-%d')} "
                f"< expected_end={expected_end}."
            )


def check_cache_coverage(df: pd.DataFrame, start_date: str, end_date: str | None) -> bool:
    """Kiểm tra DataFrame từ cache có bao phủ đủ khoảng ngày yêu cầu không."""
    if df is None or df.empty or "Date" not in df.columns:
        return False
    min_d = df["Date"].min()
    max_d = df["Date"].max()
    target_start = pd.to_datetime(start_date)

    if min_d > target_start + pd.Timedelta(days=4):
        return False

    if end_date is not None:
        target_end = pd.to_datetime(end_date)
    else:
        target_end = pd.to_datetime(get_target_market_date())

    if max_d < target_end:
        return False

    return True


def _atomic_save_parquet(df: pd.DataFrame, target_path: Path) -> None:
    """Ghi DataFrame ra file Parquet theo cơ chế nguyên tử (atomic write qua file tạm .tmp)."""
    tmp_path = target_path.with_name(f"{target_path.name}.tmp_{int(time.time() * 1000)}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(tmp_path, index=False, engine="pyarrow")
        tmp_path.replace(target_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def clean_stock_data(df: pd.DataFrame, symbol: str | None = None) -> pd.DataFrame:
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
        "Giá sàn": "Low",  # Alias tương thích ngược
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

    expected_cols = [
        c
        for c in ["Date", "Symbol", "Open", "High", "Low", "Close", "Volume"]
        if c in data.columns
    ]
    other_cols = [c for c in data.columns if c not in expected_cols]
    return data[expected_cols + other_cols]


def load_local_data(
    symbol: str = DEFAULT_SYMBOL,
    data_dir: Path = RAW_DATA_DIR,
) -> pd.DataFrame | None:
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
    end_date: str | None = None,
    save_to_raw: bool = True,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Tải và lưu trữ dữ liệu chỉ số thị trường (VNINDEX), tự động tính Return 1d."""
    raw_parquet_path = RAW_DATA_DIR / f"{index_id.upper()}.parquet"
    raw_csv_path = RAW_DATA_DIR / f"{index_id.upper()}.csv"
    effective_end = end_date or get_default_end_date()

    if not force_refresh:
        cached_df = None
        if raw_parquet_path.exists():
            cached_df = pd.read_parquet(raw_parquet_path)
        elif raw_csv_path.exists():
            cached_df = pd.read_csv(raw_csv_path)

        if cached_df is not None and not cached_df.empty:
            cached_df["Date"] = pd.to_datetime(cached_df["Date"])
            # Kiểm tra bao phủ cache
            if check_cache_coverage(cached_df, start_date=start_date, end_date=effective_end):
                ret_col = f"{index_id.upper()}_Return_1d"
                if ret_col not in cached_df.columns:
                    cached_df[ret_col] = cached_df[f"{index_id.upper()}_Close"].pct_change(1)
                return cached_df
            elif cached_df["Date"].max() < pd.to_datetime(effective_end):
                # Thử gọi API cho đoạn (max_date + 1, effective_end] xem có phiên mới không
                max_cache_date = cached_df["Date"].max()
                next_start = (max_cache_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
                try:
                    ssi_client = SSIFastConnectClient()
                    tail_df = ssi_client.get_daily_index(
                        index_id=index_id, start_date=next_start, end_date=effective_end
                    )
                    if tail_df.empty:
                        # Đoạn cuối không có phiên giao dịch mới -> Cache HIT
                        ret_col = f"{index_id.upper()}_Return_1d"
                        if ret_col not in cached_df.columns:
                            cached_df[ret_col] = cached_df[f"{index_id.upper()}_Close"].pct_change(
                                1
                            )
                        return cached_df
                    else:
                        # Ghép nến mới vào cache hiện tại (chỉ giữ nến hợp lệ Close > 0, ưu tiên bản ghi mới hơn)
                        close_col = f"{index_id.upper()}_Close"
                        valid_tail = tail_df.dropna(subset=[close_col]).copy()
                        valid_tail = valid_tail[valid_tail[close_col] > 0]
                        if not valid_tail.empty:
                            combined = pd.concat([cached_df, valid_tail], ignore_index=True)
                            combined = combined.drop_duplicates(subset=["Date"], keep="last").sort_values("Date").reset_index(drop=True)
                            ret_col = f"{index_id.upper()}_Return_1d"
                            combined[ret_col] = combined[close_col].pct_change(1)
                            validate_downloaded_data(
                                combined,
                                expected_start=start_date,
                                expected_end=effective_end,
                                is_index=True,
                                symbol_name=index_id,
                            )
                            if save_to_raw:
                                _atomic_save_parquet(combined, raw_parquet_path)
                            return combined
                        return cached_df
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Không thể kiểm tra đoạn ngày mới cho %s: %s. Fallback tải lại toàn bộ.",
                        index_id,
                        exc,
                    )

    # Tải mới toàn bộ từ API
    ssi_client = SSIFastConnectClient()
    df = ssi_client.get_daily_index(index_id=index_id, start_date=start_date, end_date=effective_end)
    validate_downloaded_data(
        df, expected_start=start_date, expected_end=effective_end, is_index=True, symbol_name=index_id
    )

    df[f"{index_id.upper()}_Return_1d"] = df[f"{index_id.upper()}_Close"].pct_change(1)

    if save_to_raw:
        _atomic_save_parquet(df, raw_parquet_path)

    return df


def fetch_stock_data(
    symbol: str = DEFAULT_SYMBOL,
    start_date: str = DEFAULT_START_DATE,
    end_date: str | None = None,
    save_to_raw: bool = True,
    force_refresh: bool = False,
    unit: str = "kVND",
) -> pd.DataFrame:
    """Tải dữ liệu OHLCV đơn mã (ưu tiên đọc Parquet cache có kiểm tra bao phủ ngày, fallback API)."""
    symbol = symbol.upper()
    effective_end = end_date or get_default_end_date()

    if not force_refresh:
        local_df = load_local_data(symbol)
        if local_df is not None and not local_df.empty:
            if check_cache_coverage(local_df, start_date=start_date, end_date=effective_end):
                return local_df
            # Nếu cache có sẵn nhưng thiếu các phiên mới nhất
            max_local_date = local_df["Date"].max()
            if max_local_date < pd.to_datetime(effective_end):
                next_start = (max_local_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
                try:
                    ssi_client = SSIFastConnectClient()
                    tail_df = ssi_client.get_daily_ohlcv(
                        symbol=symbol,
                        start_date=next_start,
                        end_date=effective_end,
                        unit=unit,
                    )
                    if not tail_df.empty:
                        cleaned_tail = clean_stock_data(tail_df, symbol=symbol)
                        cleaned_tail = cleaned_tail[cleaned_tail["Close"] > 0]
                        if not cleaned_tail.empty:
                            combined = pd.concat([local_df, cleaned_tail], ignore_index=True)
                            combined = combined.drop_duplicates(subset=["Date"], keep="last").sort_values("Date").reset_index(drop=True)
                            validate_downloaded_data(
                                combined,
                                expected_start=start_date,
                                expected_end=effective_end,
                                is_index=False,
                                symbol_name=symbol,
                            )
                            if save_to_raw:
                                parquet_path = RAW_DATA_DIR / f"{symbol}.parquet"
                                _atomic_save_parquet(combined, parquet_path)
                            return combined
                    return local_df
                except Exception as inc_exc:
                    logger.warning("Không thể kéo nến mới đoạn đuôi cho %s: %s", symbol, inc_exc)

    try:
        ssi_client = SSIFastConnectClient()
        df = ssi_client.get_daily_ohlcv(
            symbol=symbol,
            start_date=start_date,
            end_date=effective_end,
            unit=unit,
        )
        if df.empty:
            raise ValueError(f"SSI không trả về dữ liệu cho mã {symbol}")
    except Exception as exc:
        local_df = load_local_data(symbol)
        if local_df is not None and not local_df.empty:
            logger.warning("Không thể tải từ API cho %s (%s). Sử dụng cache sẵn có.", symbol, exc)
            return local_df
        raise RuntimeError(f"Lỗi thu thập dữ liệu mã {symbol}: {exc}") from exc

    cleaned_df = clean_stock_data(df, symbol=symbol)
    validate_downloaded_data(
        cleaned_df,
        expected_start=start_date,
        expected_end=effective_end,
        is_index=False,
        symbol_name=symbol,
    )

    if save_to_raw:
        parquet_path = RAW_DATA_DIR / f"{symbol}.parquet"
        _atomic_save_parquet(cleaned_df, parquet_path)

    return cleaned_df


def resolve_target_symbols(symbols: list[str] | str | None = None) -> list[str]:
    """
    Chuẩn hóa danh sách mã cổ phiếu mục tiêu:
    - None, 'VN30', 'ALL' -> Toàn bộ 30 mã VN30 (VN30_SYMBOLS)
    - 'CORE' -> 5 mã cốt lõi (DEFAULT_SYMBOLS: VIC, HPG, FPT, VNM, MWG)
    - list/tuple/set -> Danh sách mã viết hoa
    - str đơn -> [str.upper()]
    """
    if symbols is None:
        return list(VN30_SYMBOLS)
    if isinstance(symbols, str):
        sym_clean = symbols.strip().upper()
        if sym_clean in ["VN30", "ALL"]:
            return list(VN30_SYMBOLS)
        if sym_clean == "CORE":
            return list(DEFAULT_SYMBOLS)
        return [sym_clean]
    return [str(s).strip().upper() for s in symbols]


def sync_latest_market_data(
    symbols: list[str] | str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """
    Tự động đồng bộ nến thị trường mới nhất tới phiên chốt hợp lệ gần nhất (T hoặc T-1).
    - Cập nhật chỉ số thị trường (VNINDEX, VN30)
    - Cập nhật các mã được chỉ định (mặc định toàn bộ 30 mã VN30)
    - Cập nhật phân vùng Panel dataset interim
    """
    session_info = get_target_market_session_info()
    target_date = session_info["target_date"]

    logger.info(
        "Bắt đầu đồng bộ dữ liệu thị trường tới phiên %s (%s)...",
        target_date,
        session_info["session_name"],
    )
    synced_symbols = []
    errors = {}

    # 1. Đồng bộ các chỉ số thị trường chính
    for idx_id in ["VNINDEX", "VN30"]:
        try:
            fetch_daily_index(index_id=idx_id, end_date=target_date, force_refresh=force)
            synced_symbols.append(idx_id)
        except Exception as exc:
            logger.warning("Lỗi đồng bộ chỉ số %s: %s", idx_id, exc)
            errors[idx_id] = str(exc)

    # 2. Đồng bộ các mã chỉ định
    target_list = resolve_target_symbols(symbols)
    for sym in target_list:
        try:
            fetch_stock_data(symbol=sym, end_date=target_date, force_refresh=force)
            synced_symbols.append(sym)
        except Exception as exc:
            logger.warning("Lỗi đồng bộ mã %s: %s", sym, exc)
            errors[sym] = str(exc)

    # 3. Xây dựng lại panel nếu đồng bộ thành công
    try:
        build_panel_dataset(symbols=target_list, end_date=target_date, force_refresh=False)
    except Exception as exc:
        logger.warning("Lỗi cập nhật panel interim sau đồng bộ: %s", exc)

    return {
        "status": "success" if not errors else "partial",
        "target_date": target_date,
        "session_info": session_info,
        "synced_symbols": synced_symbols,
        "errors": errors,
    }


def build_panel_dataset(
    symbols: list[str] | str | None = None,
    start_date: str = DEFAULT_START_DATE,
    end_date: str | None = DEFAULT_END_DATE,
    save_to_interim: bool = True,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Thu thập dữ liệu đa mã, tích hợp chỉ số VN-Index và lưu dạng Parquet phân vùng theo Symbol.

    Args:
        symbols: Danh sách mã, hoặc 'VN30'/'ALL' (30 mã VN30), 'CORE' (5 mã cốt lõi), hoặc None (toàn bộ VN30).
        start_date: Ngày bắt đầu.
        end_date: Ngày kết thúc.
        save_to_interim: Lưu phân vùng Parquet vào data/interim/panel/.
        force_refresh: Bắt buộc tải lại từ API thay vì đọc cache.
    """
    target_symbols = resolve_target_symbols(symbols)

    dfs: list[pd.DataFrame] = []
    for sym in target_symbols:
        df_sym = fetch_stock_data(
            symbol=sym,
            start_date=start_date,
            end_date=end_date,
            force_refresh=force_refresh,
        )
        if not check_cache_coverage(df_sym, start_date=start_date, end_date=end_date):
            raise InsufficientDataCoverageError(
                f"Mã {sym} không bao phủ đủ dải ngày yêu cầu [{start_date} -> {end_date}]. Dừng tạo panel."
            )
        # Lọc đúng dải ngày yêu cầu để đồng bộ nhất quán với chỉ số VN-Index
        effective_end = end_date or get_default_end_date()
        df_sym_filtered = df_sym.copy()
        df_sym_filtered["Date"] = pd.to_datetime(df_sym_filtered["Date"])
        df_sym_filtered = df_sym_filtered[
            (df_sym_filtered["Date"] >= pd.to_datetime(start_date))
            & (df_sym_filtered["Date"] <= pd.to_datetime(effective_end))
        ].sort_values("Date").reset_index(drop=True)
        dfs.append(df_sym_filtered)

    panel_df = pd.concat(dfs, ignore_index=True)
    panel_df = panel_df.sort_values(["Date", "Symbol"]).reset_index(drop=True)

    # Tích hợp chỉ số toàn thị trường VN-Index
    df_vnindex = fetch_daily_index(
        index_id="VNINDEX",
        start_date=start_date,
        end_date=end_date,
        force_refresh=force_refresh,
    )

    # Kiểm tra VNINDEX phủ đủ mọi ngày của mọi mã cổ phiếu
    stock_dates = set(panel_df["Date"].unique())
    vni_dates = set(df_vnindex["Date"].unique())
    missing_in_vni = stock_dates - vni_dates
    if missing_in_vni:
        raise ValueError(
            f"Dữ liệu VNINDEX thiếu {len(missing_in_vni)} ngày so với các mã cổ phiếu trong panel: "
            f"{sorted(missing_in_vni)[:10]}"
        )

    # Ngược lại, nếu ngày VNINDEX không có ở mã nào -> cảnh báo
    for sym in target_symbols:
        sym_dates = set(panel_df[panel_df["Symbol"] == sym]["Date"].unique())
        missing_in_sym = vni_dates - sym_dates
        if missing_in_sym:
            logger.warning(
                "Mã %s thiếu %d ngày so với lịch VNINDEX trong dải ngày: %s",
                sym,
                len(missing_in_sym),
                sorted(missing_in_sym)[:5],
            )

    # Cảnh báo (không chặn) nếu có |lợi suất ngày| > 7.5% (biên độ giá HOSE +-7%)
    for sym in target_symbols:
        sub = panel_df[panel_df["Symbol"] == sym].sort_values("Date").copy()
        sub["Ret_1d"] = sub["Close"].pct_change(1)
        extreme_rows = sub[sub["Ret_1d"].abs() > 0.075]
        if not extreme_rows.empty:
            dates_str = [d.strftime("%Y-%m-%d") for d in extreme_rows["Date"]]
            logger.warning(
                "Mã %s có %d phiên có |lợi suất ngày| > 7.5%% (biên độ HOSE): %s",
                sym,
                len(extreme_rows),
                dates_str[:5],
            )

    panel_df = pd.merge(
        panel_df,
        df_vnindex[["Date", "VNINDEX_Return_1d"]],
        on="Date",
        how="left",
    )

    if save_to_interim:
        PANEL_DATA_DIR.parent.mkdir(parents=True, exist_ok=True)
        tmp_panel_dir = PANEL_DATA_DIR.parent / f"panel_tmp_{int(time.time() * 1000)}"
        old_panel_dir = PANEL_DATA_DIR.parent / f"panel_old_{int(time.time() * 1000)}"
        try:
            tmp_panel_dir.mkdir(parents=True, exist_ok=True)
            panel_df.to_parquet(
                tmp_panel_dir,
                partition_cols=["Symbol"],
                engine="pyarrow",
                index=False,
            )
            # Kiểm tra đọc lại từ thư mục tạm trước khi hoán đổi
            check_df = pd.read_parquet(tmp_panel_dir, engine="pyarrow")
            if len(check_df) != len(panel_df):
                raise RuntimeError(
                    f"Thư mục tạm panel ghi thiếu dữ liệu: {len(check_df)} != {len(panel_df)} dòng."
                )

            if PANEL_DATA_DIR.exists():
                PANEL_DATA_DIR.rename(old_panel_dir)
            tmp_panel_dir.rename(PANEL_DATA_DIR)

            if old_panel_dir.exists():
                shutil.rmtree(old_panel_dir)
        finally:
            if tmp_panel_dir.exists():
                shutil.rmtree(tmp_panel_dir)

    return panel_df


def load_panel_dataset(
    symbols: list[str] | None = None,
    panel_dir: Path = PANEL_DATA_DIR,
) -> pd.DataFrame:
    """Nạp nhanh dữ liệu Long-format từ thư mục Parquet phân vùng theo danh sách mã."""
    if not panel_dir.exists():
        raise FileNotFoundError(
            f"Chưa có dữ liệu panel tại {panel_dir}. Hãy gọi build_panel_dataset() trước."
        )

    filters = None
    if symbols is not None and len(symbols) > 0:
        clean_symbols = [s.upper() for s in symbols]
        filters = [("Symbol", "in", clean_symbols)]

    df = pd.read_parquet(panel_dir, filters=filters, engine="pyarrow")
    if "Symbol" in df.columns:
        df["Symbol"] = df["Symbol"].astype(str)
    return df.sort_values(["Date", "Symbol"]).reset_index(drop=True)
