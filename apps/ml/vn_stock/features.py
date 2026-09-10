"""Module tính toán các chỉ báo kỹ thuật tài chính và trích xuất đặc trưng (Feature Engineering)."""

from typing import List, Tuple
import numpy as np
import pandas as pd


def compute_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Tính toán bộ chỉ báo kỹ thuật cơ bản và nâng cao từ dữ liệu OHLCV."""
    data = df.copy()

    # Tìm các cột giá tương ứng
    close_col = "Close" if "Close" in data.columns else "Giá đóng cửa"
    open_col = "Open" if "Open" in data.columns else "Giá mở cửa"
    high_col = "High" if "High" in data.columns else "Giá trần"
    low_col = "Low" if "Low" in data.columns else "Giá sàn"

    # Chênh lệch giá
    if high_col in data.columns and low_col in data.columns:
        data["H-L"] = data[high_col] - data[low_col]
    if open_col in data.columns and close_col in data.columns:
        data["O-C"] = data[open_col] - data[close_col]

    # Các đường trung bình động Simple Moving Average (SMA)
    if close_col in data.columns:
        data["SMA_20"] = data[close_col].rolling(window=20).mean()
        data["SMA_50"] = data[close_col].rolling(window=50).mean()
        data["SMA_200"] = data[close_col].rolling(window=200).mean()

        # Độ lệch chuẩn (Standard Deviation)
        data["SD_50"] = data[close_col].rolling(window=50).std()
        data["SD_200"] = data[close_col].rolling(window=200).std()

        # Dải Bollinger Bands (20 ngày, 2 độ lệch chuẩn)
        data["BB_Mid"] = data["SMA_20"]
        data["BB_Upper"] = data["BB_Mid"] + (2 * data[close_col].rolling(window=20).std())
        data["BB_Lower"] = data["BB_Mid"] - (2 * data[close_col].rolling(window=20).std())

        # Chỉ số sức mạnh tương đối RSI (14 ngày)
        delta = data[close_col].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=14, min_periods=1).mean()
        avg_loss = loss.rolling(window=14, min_periods=1).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        data["RSI"] = 100 - (100 / (1 + rs))
        data["RSI"] = data["RSI"].fillna(50.0)

    return data


def create_sequences(
    data: np.ndarray,
    seq_length: int = 30,
) -> Tuple[np.ndarray, np.ndarray]:
    """Tạo chuỗi trượt thời gian (time-series sliding windows) cho mô hình LSTM."""
    xs: List[np.ndarray] = []
    ys: List[np.ndarray] = []
    for i in range(len(data) - seq_length):
        x = data[i : (i + seq_length)]
        y = data[i + seq_length]
        xs.append(x)
        ys.append(y)
    return np.array(xs), np.array(ys)
