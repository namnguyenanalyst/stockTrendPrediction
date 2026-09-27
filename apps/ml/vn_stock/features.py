"""Module tính toán bộ 13 đặc trưng tương đối và tạo chuỗi 3D đa biến có Warm-up cho mô hình Global Model."""

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd

from vn_stock.config import DEFAULT_SEQ_LENGTH, SYMBOL_TO_CODE

# Danh sách 13 đặc trưng số học tương đối (không dùng giá/khối lượng tuyệt đối)
FEATURE_COLS = [
    "Open_Close_Ratio",
    "High_Close_Ratio",
    "Low_Close_Ratio",
    "HL_Ratio",
    "SMA_20_Dev",
    "SMA_50_Dev",
    "SMA_200_Dev",
    "CV_50",
    "CV_200",
    "RSI",
    "Return_1d",
    "Vol_Ratio",
    "VNINDEX_Return_1d",
]

# Danh sách đầy đủ 14 đặc trưng đưa vào huấn luyện Global Model (13 số học + 1 mã hóa symbol)
ALL_FEATURE_COLS = FEATURE_COLS + ["Symbol_Code"]


def _compute_for_single_stock(group: pd.DataFrame) -> pd.DataFrame:
    """Tính toán 12 đặc trưng tương đối cho một mã cổ phiếu độc lập (tránh data leakage)."""
    g = group.sort_values("Date").copy()

    close = g["Close"]
    open_p = g["Open"]
    high = g["High"]
    low = g["Low"]
    volume = g["Volume"]

    # 1. Các tỷ lệ tương đối so với giá đóng cửa cùng ngày
    g["Open_Close_Ratio"] = (open_p - close) / close
    g["High_Close_Ratio"] = (high - close) / close
    g["Low_Close_Ratio"] = (low - close) / close
    g["HL_Ratio"] = (high - low) / close

    # 2. Độ lệch tương đối so với Simple Moving Average (SMA)
    sma_20 = close.rolling(window=20).mean()
    sma_50 = close.rolling(window=50).mean()
    sma_200 = close.rolling(window=200).mean()
    g["SMA_20_Dev"] = (close - sma_20) / sma_20
    g["SMA_50_Dev"] = (close - sma_50) / sma_50
    g["SMA_200_Dev"] = (close - sma_200) / sma_200

    # 3. Hệ số biến thiên rủi ro (Coefficient of Variation: CV = SD / SMA)
    sd_50 = close.rolling(window=50).std()
    sd_200 = close.rolling(window=200).std()
    g["CV_50"] = sd_50 / (sma_50 + 1e-9)
    g["CV_200"] = sd_200 / (sma_200 + 1e-9)

    # 4. Chỉ số sức mạnh tương đối RSI (chu kỳ 14 ngày chuẩn)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    g["RSI"] = 100.0 - (100.0 / (1.0 + rs))

    # 5. Tỷ suất lợi nhuận quá khứ 1 phiên (Return_1d tính lùi làm feature)
    g["Return_1d"] = (close - close.shift(1)) / close.shift(1)

    # 6. Biến động khối lượng tương đối so với SMA khối lượng 20 phiên
    vol_sma_20 = volume.rolling(window=20).mean()
    g["Vol_Ratio"] = volume / (vol_sma_20 + 1e-9)

    return g


def compute_features_per_symbol(
    df: pd.DataFrame,
    drop_na: bool = True,
) -> pd.DataFrame:
    """
    Tính toán bộ đặc trưng tương đối độc lập theo từng mã bằng groupby('Symbol').
    
    Args:
        df: DataFrame Long-format (bắt buộc có Date, Symbol, Open, High, Low, Close, Volume, VNINDEX_Return_1d)
        drop_na: Nếu True, loại bỏ các dòng có NaN do cửa sổ rolling 200 phiên ban đầu.
    """
    df_in = df.copy()
    if "Symbol" not in df_in.columns:
        raise ValueError("DataFrame phải chứa cột 'Symbol' để tính đặc trưng theo mã.")

    # Đảm bảo có cột VNINDEX_Return_1d (đưa thẳng vào danh sách feature)
    if "VNINDEX_Return_1d" not in df_in.columns:
        df_in["VNINDEX_Return_1d"] = 0.0

    # Áp dụng tính toán độc lập theo từng mã bằng groupby('Symbol')
    dfs = [_compute_for_single_stock(group) for _, group in df_in.groupby("Symbol")]
    res = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    # Gán Symbol_Code cố định dựa theo SYMBOL_TO_CODE trong config
    res["Symbol_Code"] = res["Symbol"].map(SYMBOL_TO_CODE).fillna(-1).astype(int)

    if drop_na:
        # Loại bỏ các dòng NaN do rolling 200 ngày và pct_change ngày đầu tiên
        res = res.dropna(subset=FEATURE_COLS).reset_index(drop=True)

    return res


def create_multivariate_sequences(
    df: pd.DataFrame,
    warmup_df: Optional[pd.DataFrame] = None,
    feature_cols: List[str] = ALL_FEATURE_COLS,
    seq_length: int = DEFAULT_SEQ_LENGTH,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Tạo chuỗi trượt 3D đa biến cho PyTorch LSTM với cơ chế Warm-up bảo toàn mẫu.
    
    Args:
        df: Tập dữ liệu chính (train, val hoặc test)
        warmup_df: Tập dữ liệu liền trước (ví dụ lấy đuôi train làm warm-up cho val/test)
        feature_cols: Danh sách các cột đặc trưng đưa vào chuỗi 3D
        seq_length: Độ dài chuỗi quan sát quá khứ (mặc định 20 phiên)
        
    Returns:
        xs: Mảng numpy 3D shape (N, seq_length, len(feature_cols)) dạng float32
        ys: Mảng numpy 1D shape (N,) dạng int64 (nếu có cột Label, ngược lại None)
    """
    xs, ys = [], []
    has_label = "Label" in df.columns

    for sym in df["Symbol"].unique():
        curr_sym = df[df["Symbol"] == sym].sort_values("Date")
        if warmup_df is not None and not warmup_df.empty and sym in warmup_df["Symbol"].values:
            warm_sym = warmup_df[warmup_df["Symbol"] == sym].sort_values("Date").tail(seq_length)
            combined = pd.concat([warm_sym, curr_sym], ignore_index=True)
            start_idx = len(warm_sym)
        else:
            combined = curr_sym
            start_idx = seq_length

        features = combined[feature_cols].values
        labels = combined["Label"].values if has_label else None

        for i in range(start_idx, len(combined)):
            xs.append(features[i - seq_length : i])
            if has_label:
                ys.append(labels[i])

    x_arr = np.array(xs, dtype=np.float32)
    y_arr = np.array(ys, dtype=np.int64) if has_label else None

    return x_arr, y_arr
