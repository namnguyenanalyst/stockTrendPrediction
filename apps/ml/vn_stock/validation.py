"""Module phân chia dữ liệu chuỗi thời gian và kiểm định chéo (Walk-Forward Validation)."""

from typing import Tuple, Generator
import numpy as np
import pandas as pd


def time_series_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Phân chia dữ liệu tuần tự theo thời gian: Train / Validation / Test.
    Tuyệt đối không xáo trộn (no shuffle) để ngăn ngừa rò rỉ thông tin tương lai (Look-ahead bias).
    """
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train_df = df.iloc[:train_end].copy()
    val_df = df.iloc[train_end:val_end].copy()
    test_df = df.iloc[val_end:].copy()

    return train_df, val_df, test_df


def walk_forward_splits(
    df: pd.DataFrame,
    n_splits: int = 5,
    min_train_size: int = 200,
    test_size: int = 50,
) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
    """
    Tạo các lát cắt Walk-Forward mở rộng dần (Expanding Window Walk-Forward).
    Mỗi bước kiểm tra mô hình trên tập tương lai chưa từng nhìn thấy.
    """
    total_len = len(df)
    start_test = total_len - (n_splits * test_size)
    if start_test < min_train_size:
        start_test = min_train_size

    for i in range(n_splits):
        split_idx = start_test + (i * test_size)
        if split_idx >= total_len:
            break
        train_part = df.iloc[:split_idx]
        test_part = df.iloc[split_idx : split_idx + test_size]
        yield train_part, test_part
