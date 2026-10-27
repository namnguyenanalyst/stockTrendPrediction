"""Module tiền xử lý, gán nhãn đa phiên T+3 (Purged Horizon) và phân chia dữ liệu huấn luyện thực chiến (Production Retraining)."""

import logging
from typing import Any
import warnings

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from vn_stock.config import DEFAULT_SEQ_LENGTH, STUDY_START_DATE
from vn_stock.features import FEATURE_COLS

logger = logging.getLogger(__name__)


def apply_study_window(
    df: pd.DataFrame,
    start_date: str = STUDY_START_DATE,
    date_col: str = "Date",
) -> pd.DataFrame:
    """
    Cắt gọn tập dữ liệu bảng đa mã về đúng phạm vi cửa sổ nghiên cứu (Study Window).

    Lý do tồn tại hàm:
    - Trong pipeline ML, dữ liệu giá thô cần được thu thập từ FETCH_START_DATE (2022-01-01)
      để cung cấp ~250 phiên giao dịch khởi động (warm-up history) cho các chỉ báo kỹ thuật có cửa sổ
      dài như SMA_200 và CV_200.
    - Hàm compute_features_per_symbol(drop_na=True) phải được tính trên TOÀN BỘ lịch sử này để không
      bị mất các phiên đầu năm 2023.
    - Sau khi đã tính xong đầy đủ đặc trưng, hàm apply_study_window() được gọi để cắt gọn lại dữ liệu,
      chỉ giữ các phiên từ STUDY_START_DATE (2023-01-04) trở đi. Nhờ đó:
      (a) Các đặc trưng kỹ thuật rolling đã hội tụ đầy đủ giá trị ngay từ ngày 2023-01-04 cho cả 5 mã.
      (b) Dữ liệu huấn luyện thực chiến được tính toán nghiêm ngặt trên đúng
          tập các ngày của cửa sổ nghiên cứu, bảo đảm tính nhất quán và chất lượng đặc trưng.

    Args:
        df: DataFrame chứa dữ liệu đặc trưng đã tính toán.
        start_date: Ngày bắt đầu cửa sổ nghiên cứu (mặc định STUDY_START_DATE = "2023-01-04").
        date_col: Tên cột thời gian (mặc định 'Date').

    Returns:
        pd.DataFrame chỉ chứa các dòng có Date >= start_date, đã sắp xếp theo Date và Symbol.
    """
    if date_col not in df.columns:
        raise ValueError(f"DataFrame phải chứa cột '{date_col}' để áp dụng cửa sổ nghiên cứu.")

    target_dt = pd.to_datetime(start_date)
    filtered = df[df[date_col] >= target_dt].copy()

    sort_cols = [date_col]
    if "Symbol" in filtered.columns:
        sort_cols.append("Symbol")

    return filtered.sort_values(sort_cols).reset_index(drop=True)


def create_labels_per_symbol(
    df: pd.DataFrame,
    threshold: float = 0.01,
    horizon: int = 1,
    close_col: str = "Close",
    symbol_col: str = "Symbol",
    date_col: str = "Date",
) -> pd.DataFrame:
    """
    Tạo nhãn xu hướng 3 lớp có ngưỡng độc lập theo từng mã cổ phiếu (mặc định horizon=1 cho tương thích ngược).
    Khuyến nghị sử dụng trực tiếp `create_multi_day_labels` cho các pipeline thực chiến T+3 (horizon=3, threshold=0.02).

    Công thức:
        Next_Return = (Close(t+horizon) - Close(t)) / Close(t)
        - Nhãn 0 (Giảm): Next_Return <= -threshold
        - Nhãn 1 (Đi ngang): -threshold < Next_Return < threshold
        - Nhãn 2 (Tăng): Next_Return >= threshold

    Args:
        df: DataFrame chứa dữ liệu đa mã.
        threshold: Ngưỡng lọc nhiễu nhãn xu hướng (mặc định 0.01 tương ứng +-1.0%).
        horizon: Số phiên nhìn về tương lai (mặc định 1 cho T+1).
        close_col: Tên cột giá đóng cửa.
        symbol_col: Tên cột mã cổ phiếu.
        date_col: Tên cột ngày giao dịch.

    Returns:
        pd.DataFrame đã có thêm cột 'Label' (kiểu int64) và 'Target_Return'.
    """
    return create_multi_day_labels(
        df=df,
        horizon=horizon,
        threshold=threshold,
        close_col=close_col,
        symbol_col=symbol_col,
        date_col=date_col,
    )


def drop_ignored_labels(X: Any, y: np.ndarray) -> tuple[Any, np.ndarray]:
    """
    Hàm lọc tiện ích dùng chung: loại bỏ triệt để các mẫu mang nhãn sentinel -1 (purged boundary)
    trước khi đưa vào huấn luyện mô hình (LSTM, LightGBM, Naive) hoặc tính toán ma trận nhầm lẫn / F1.

    Args:
        X: Mảng đặc trưng 3D của LSTM (ndarray), mảng 2D (ndarray) hoặc DataFrame của LightGBM.
        y: Mảng 1D nhãn mục tiêu (ndarray).

    Returns:
        tuple[X_valid, y_valid] chỉ chứa các mẫu có nhãn hợp lệ (y != -1).
    """
    valid_mask = y != -1
    if isinstance(X, pd.DataFrame):
        X_valid = X.loc[valid_mask].reset_index(drop=True)
    elif isinstance(X, np.ndarray):
        X_valid = X[valid_mask]
    else:
        # Hỗ trợ list hoặc cấu trúc sequence khác
        X_valid = [x for idx, x in enumerate(X) if valid_mask[idx]]

    y_valid = y[valid_mask]
    return X_valid, y_valid



def scale_window(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str] = FEATURE_COLS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, StandardScaler]:
    """
    Chuẩn hóa StandardScaler độc lập chống rò rỉ thông tin (Leak-free Preprocessing).

    Quy tắc:
    - StandardScaler CHỈ được fit trên train_df[feature_cols].
    - Transform cho cả 3 tập (train, val, test) bằng scaler đã fit từ train.
    - Cột 'Symbol_Code' (và các cột định danh khác: Symbol, Date, Label, Valid_Label) TUYỆT ĐỐI KHÔNG SCALE,
      được giữ nguyên vẹn giá trị và kiểu dữ liệu gốc.

    Args:
        train_df: DataFrame tập train.
        val_df: DataFrame tập val.
        test_df: DataFrame tập test.
        feature_cols: Danh sách các cột đặc trưng số học cần chuẩn hóa (mặc định 13 cột FEATURE_COLS).

    Returns:
        tuple[train_scaled, val_scaled, test_scaled, scaler]
    """
    missing_cols = [c for c in feature_cols if c not in train_df.columns]
    if missing_cols:
        raise ValueError(f"Tập Train thiếu các cột đặc trưng bắt buộc: {missing_cols}")

    scaler = StandardScaler()
    scaler.fit(train_df[feature_cols])

    train_scaled = train_df.copy()
    val_scaled = val_df.copy()
    test_scaled = test_df.copy()

    train_scaled[feature_cols] = scaler.transform(train_df[feature_cols])

    if not val_df.empty:
        val_scaled[feature_cols] = scaler.transform(val_df[feature_cols])

    if not test_df.empty:
        test_scaled[feature_cols] = scaler.transform(test_df[feature_cols])

    return train_scaled, val_scaled, test_scaled, scaler


def get_warmup_tail(
    prev_split_df: pd.DataFrame,
    seq_length: int = DEFAULT_SEQ_LENGTH,
    symbol_col: str = "Symbol",
    date_col: str = "Date",
) -> pd.DataFrame:
    """
    Trích xuất đúng (seq_length - 1) dòng cuối cùng của MỖI MÃ CỔ PHIẾU từ tập dữ liệu liền trước.

    Dùng làm warmup_df truyền vào create_multivariate_sequences(df, warmup_df=...) trong features.py
    nhằm bảo toàn 100% số mẫu cho tập tiếp theo (Validation hoặc Test) khi chuỗi quan sát kết thúc đúng
    tại ngày thứ i.

    Args:
        prev_split_df: DataFrame của tập liền trước (ví dụ train_scaled hoặc val_scaled).
        seq_length: Độ dài chuỗi quan sát quá khứ (số dòng đuôi cần lấy là seq_length - 1).
        symbol_col: Tên cột mã cổ phiếu.
        date_col: Tên cột ngày giao dịch.

    Returns:
        pd.DataFrame chứa phần đuôi warmup của từng mã, giữ nguyên cấu trúc cột.
    """
    if prev_split_df.empty:
        return pd.DataFrame(columns=prev_split_df.columns)

    if symbol_col not in prev_split_df.columns or date_col not in prev_split_df.columns:
        raise ValueError(f"prev_split_df phải chứa cột '{symbol_col}' và '{date_col}'.")

    warmup_len = seq_length - 1
    if warmup_len <= 0:
        return pd.DataFrame(columns=prev_split_df.columns)

    tails = []
    for sym, grp in prev_split_df.groupby(symbol_col):
        sorted_grp = grp.sort_values(date_col)
        n_rows = len(sorted_grp)
        if n_rows < warmup_len:
            warnings.warn(
                f"Mã {sym} trong tập trước chỉ có {n_rows} dòng, ít hơn warmup_len={warmup_len}. "
                f"Warmup cho mã này sẽ không đủ {warmup_len} bước quan sát.",
                UserWarning,
                stacklevel=2,
            )
        tails.append(sorted_grp.tail(warmup_len))

    if not tails:
        return pd.DataFrame(columns=prev_split_df.columns)

    warmup_df = pd.concat(tails, ignore_index=True)
    return warmup_df


def create_multi_day_labels(
    df: pd.DataFrame,
    horizon: int = 3,
    threshold: float = 0.02,
    close_col: str = "Close",
    symbol_col: str = "Symbol",
    date_col: str = "Date",
) -> pd.DataFrame:
    """
    Gán nhãn xu hướng đa phiên (Multi-day Trend Labeling) cho bài toán thực tế:
    - Return_{t+horizon} = (Close_{t+horizon} - Close_t) / Close_t
    - Label = 2 (TĂNG) nếu Return >= +threshold (+2.0%)
    - Label = 0 (GIẢM) nếu Return <= -threshold (-2.0%)
    - Label = 1 (ĐI NGANG) nếu -threshold < Return < +threshold
    - Loại bỏ đúng horizon dòng cuối cùng của từng mã vì chưa diễn ra các phiên tương lai để biết nhãn.
    """
    if close_col not in df.columns:
        raise ValueError(f"DataFrame phải chứa cột giá đóng cửa '{close_col}'.")
    if symbol_col not in df.columns or date_col not in df.columns:
        raise ValueError(f"DataFrame phải chứa cột '{symbol_col}' và '{date_col}'.")

    dfs = []
    for _, grp in df.groupby(symbol_col):
        g = grp.sort_values(date_col).copy()
        next_close = g[close_col].shift(-horizon)
        next_return = (next_close - g[close_col]) / g[close_col]

        conditions = [
            next_return <= -threshold,
            (next_return > -threshold) & (next_return < threshold),
            next_return >= threshold,
        ]
        g["Label"] = np.select(conditions, [0, 1, 2], default=np.nan)
        g["Target_Return"] = next_return
        g = g.dropna(subset=["Label"]).reset_index(drop=True)
        g["Label"] = g["Label"].astype(int)
        dfs.append(g)

    if not dfs:
        return pd.DataFrame(columns=list(df.columns) + ["Label", "Target_Return"])

    res = pd.concat(dfs, ignore_index=True)
    return res.sort_values([date_col, symbol_col]).reset_index(drop=True)


def prepare_production_training_data(
    df: pd.DataFrame,
    val_buffer_days: int = 40,
    feature_cols: list[str] = FEATURE_COLS,
    seq_length: int = DEFAULT_SEQ_LENGTH,
    date_col: str = "Date",
    symbol_col: str = "Symbol",
) -> dict[str, Any]:
    """
    Chuẩn bị dữ liệu huấn luyện thực chiến (Production Retraining):
    - Sử dụng TOÀN BỘ dữ liệu lịch sử tích lũy từ STUDY_START_DATE đến phiên gần nhất có nhãn.
    - Dành val_buffer_days phiên gần nhất (mặc định 40 phiên ~ 2 tháng) làm Validation Buffer
      để phục vụ Early Stopping chống quá khớp (overfitting).
    - Toàn bộ dữ liệu trước đó (hơn 95% lịch sử) làm Train.
    - StandardScaler chỉ fit trên tập Train, sau đó transform cho cả Train và Val.
    - Trích xuất đuôi warm-up (seq_length - 1 phiên) từ Train cho Val để bảo toàn 100% mẫu cho PyTorch LSTM.
    """
    unique_dates = np.sort(df[date_col].unique())
    n_dates = len(unique_dates)

    if n_dates <= val_buffer_days:
        raise ValueError(
            f"Tổng số ngày ({n_dates}) không đủ để tạo validation buffer {val_buffer_days} ngày."
        )

    t_end_idx = n_dates - val_buffer_days
    train_dates = unique_dates[:t_end_idx]
    val_dates = unique_dates[t_end_idx:]

    train_df = df[df[date_col].isin(train_dates)].copy()
    val_df = df[df[date_col].isin(val_dates)].copy()

    train_s, val_s, _, scaler = scale_window(
        train_df=train_df,
        val_df=val_df,
        test_df=pd.DataFrame(columns=train_df.columns),
        feature_cols=feature_cols,
    )

    val_warmup = get_warmup_tail(
        prev_split_df=train_s,
        seq_length=seq_length,
        symbol_col=symbol_col,
        date_col=date_col,
    )

    return {
        "train": train_s,
        "val": val_s,
        "val_warmup": val_warmup,
        "scaler": scaler,
        "train_end_date": pd.Timestamp(train_dates[-1]),
        "val_end_date": pd.Timestamp(val_dates[-1]),
        "total_training_days": n_dates,
        "val_buffer_days": val_buffer_days,
    }

