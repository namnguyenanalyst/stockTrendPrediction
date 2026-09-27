"""Kiểm thử tính toán bộ đặc trưng tương đối và tạo chuỗi 3D đa biến có Warm-up."""

import numpy as np
import pandas as pd
import pytest

from vn_stock.config import SYMBOL_TO_CODE
from vn_stock.features import (
    ALL_FEATURE_COLS,
    FEATURE_COLS,
    compute_features_per_symbol,
    create_multivariate_sequences,
)


def test_feature_formula_calculations():
    """Kiểm thử độ chính xác của từng công thức đặc trưng tương đối với kết quả tính tay."""
    dates = pd.date_range("2024-01-01", periods=3)
    df = pd.DataFrame({
        "Date": dates,
        "Symbol": ["VIC", "VIC", "VIC"],
        "Open": [100.0, 105.0, 110.0],
        "High": [105.0, 110.0, 115.0],
        "Low": [95.0, 100.0, 105.0],
        "Close": [100.0, 108.0, 108.0],
        "Volume": [1000.0, 1500.0, 2000.0],
        "VNINDEX_Return_1d": [0.01, 0.02, -0.01],
    })

    res = compute_features_per_symbol(df, drop_na=False)

    # 1. Kiểm tra đủ 13 đặc trưng + Symbol_Code
    for col in ALL_FEATURE_COLS:
        assert col in res.columns, f"Thiếu cột đặc trưng: {col}"

    # 2. Đối chiếu tính toán phiên đầu tiên (index 0)
    # Open_Close_Ratio = (100 - 100) / 100 = 0.0
    assert pytest.approx(res.loc[0, "Open_Close_Ratio"]) == 0.0
    # High_Close_Ratio = (105 - 100) / 100 = 0.05
    assert pytest.approx(res.loc[0, "High_Close_Ratio"]) == 0.05
    # Low_Close_Ratio = (95 - 100) / 100 = -0.05
    assert pytest.approx(res.loc[0, "Low_Close_Ratio"]) == -0.05
    # HL_Ratio = (105 - 95) / 100 = 0.10
    assert pytest.approx(res.loc[0, "HL_Ratio"]) == 0.10

    # 3. Đối chiếu Return_1d tại phiên thứ 2: (108 - 100) / 100 = 0.08
    assert pytest.approx(res.loc[1, "Return_1d"]) == 0.08

    # 4. Kiểm tra mã hóa cố định Symbol_Code
    assert res.loc[0, "Symbol_Code"] == SYMBOL_TO_CODE["VIC"]


def test_groupby_symbol_no_leakage():
    """Kiểm tra rolling window và shift được cách ly 100% giữa các mã cổ phiếu."""
    dates = pd.date_range("2024-01-01", periods=5)
    # Tạo mã VIC giá ~100
    df_vic = pd.DataFrame({
        "Date": dates,
        "Symbol": ["VIC"] * 5,
        "Open": [100.0] * 5,
        "High": [105.0] * 5,
        "Low": [95.0] * 5,
        "Close": [100.0, 102.0, 104.0, 106.0, 108.0],
        "Volume": [1000.0] * 5,
        "VNINDEX_Return_1d": [0.01] * 5,
    })
    # Tạo mã HPG giá ~20 (rất khác VIC)
    df_hpg = pd.DataFrame({
        "Date": dates,
        "Symbol": ["HPG"] * 5,
        "Open": [20.0] * 5,
        "High": [22.0] * 5,
        "Low": [18.0] * 5,
        "Close": [20.0, 21.0, 22.0, 23.0, 24.0],
        "Volume": [50000.0] * 5,
        "VNINDEX_Return_1d": [0.01] * 5,
    })

    # Ghép chung vào 1 bảng panel
    df_panel = pd.concat([df_vic, df_hpg], ignore_index=True)
    res_panel = compute_features_per_symbol(df_panel, drop_na=False)

    # Tính riêng rẽ cho HPG độc lập
    res_hpg_isolated = compute_features_per_symbol(df_hpg, drop_na=False)

    # Trích xuất phần HPG từ kết quả panel
    res_hpg_from_panel = res_panel[res_panel["Symbol"] == "HPG"].reset_index(drop=True)

    # Dòng đầu tiên của HPG bắt buộc Return_1d phải là NaN (không được lấy chênh lệch từ dòng cuối của VIC)
    assert np.isnan(res_hpg_from_panel.loc[0, "Return_1d"])

    # Mọi giá trị đặc trưng của HPG khi chạy trong Panel phải GIỐNG HỆT khi chạy độc lập
    for col in FEATURE_COLS:
        pd.testing.assert_series_equal(
            res_hpg_from_panel[col],
            res_hpg_isolated[col],
            check_names=False,
            obj=f"Column {col} bị rò rỉ dữ liệu giữa VIC và HPG"
        )


def test_create_multivariate_sequences_without_and_with_warmup():
    """Kiểm tra tạo tensor chuỗi 3D đa biến cho LSTM và cơ chế bảo toàn mẫu bằng Warm-up."""
    # Tạo dữ liệu giả lập cho 2 mã (VIC và HPG), mỗi mã 30 phiên
    dates = pd.date_range("2024-01-01", periods=30)
    data_list = []
    for sym in ["VIC", "HPG"]:
        for d in dates:
            row = {col: np.random.randn() for col in FEATURE_COLS}
            row["Date"] = d
            row["Symbol"] = sym
            row["Symbol_Code"] = SYMBOL_TO_CODE[sym]
            row["Label"] = np.random.choice([0, 1, 2])
            data_list.append(row)

    df_full = pd.DataFrame(data_list)
    seq_len = 20

    # 1. Trường hợp KHÔNG có warmup_df
    # Mỗi mã có 30 phiên, không có warmup sẽ mất seq_len mẫu đầu -> mỗi mã còn 30 - 20 = 10 mẫu
    # Tổng cộng 2 mã = 20 mẫu
    xs_no_warmup, ys_no_warmup = create_multivariate_sequences(
        df_full,
        warmup_df=None,
        feature_cols=ALL_FEATURE_COLS,
        seq_length=seq_len,
    )
    assert xs_no_warmup.shape == (20, seq_len, len(ALL_FEATURE_COLS))
    assert ys_no_warmup.shape == (20,)
    assert not np.isnan(xs_no_warmup).any()

    # 2. Trường hợp CÓ warmup_df (mô phỏng tập Validation / Test nhận đuôi tập trước)
    train_part = pd.concat([g.head(20) for _, g in df_full.groupby("Symbol")], ignore_index=True)
    val_part = pd.concat([g.tail(10) for _, g in df_full.groupby("Symbol")], ignore_index=True)

    # Có warmup_df (20 phiên của train_part), val_part (10 phiên mỗi mã) sẽ được bảo toàn 100% mẫu:
    # Mỗi mã giữ nguyên 10 mẫu -> Tổng cộng 2 mã = 20 mẫu sequences
    xs_warmup, ys_warmup = create_multivariate_sequences(
        val_part,
        warmup_df=train_part,
        feature_cols=ALL_FEATURE_COLS,
        seq_length=seq_len,
    )
    assert xs_warmup.shape == (20, seq_len, len(ALL_FEATURE_COLS))
    assert ys_warmup.shape == (20,)
    assert not np.isnan(xs_warmup).any()
