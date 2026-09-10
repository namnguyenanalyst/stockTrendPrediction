"""Kiểm thử tính toán chỉ báo kỹ thuật và tạo chuỗi thời gian."""

import numpy as np
import pandas as pd
from vn_stock.features import compute_technical_indicators, create_sequences


def test_compute_technical_indicators():
    # Tạo chuỗi giá mẫu 60 ngày
    dates = pd.date_range("2024-01-01", periods=60)
    prices = np.linspace(20.0, 30.0, 60)
    df = pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": prices + 1.0,
        "Low": prices - 1.0,
        "Close": prices,
        "Volume": [1000] * 60,
    })

    indicators_df = compute_technical_indicators(df)

    assert "H-L" in indicators_df.columns
    assert "O-C" in indicators_df.columns
    assert "SMA_20" in indicators_df.columns
    assert "SMA_50" in indicators_df.columns
    assert "RSI" in indicators_df.columns
    assert "BB_Upper" in indicators_df.columns

    # Kiểm tra giá trị H-L
    assert np.allclose(indicators_df["H-L"].values, 2.0)


def test_create_sequences():
    data = np.arange(10)
    seq_len = 3
    x, y = create_sequences(data, seq_length=seq_len)

    assert len(x) == len(data) - seq_len
    assert np.array_equal(x[0], [0, 1, 2])
    assert y[0] == 3
    assert np.array_equal(x[-1], [6, 7, 8])
    assert y[-1] == 9
