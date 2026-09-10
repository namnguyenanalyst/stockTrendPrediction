"""Kiểm thử cho module dataset."""

import pandas as pd
from vn_stock.dataset import clean_stock_data, load_local_data


def test_clean_stock_data():
    df_raw = pd.DataFrame({
        "yyyy-mm-dd": ["2024-01-02", "2024-01-01"],
        "Giá mở cửa": [20.0, 19.5],
        "Giá đóng cửa": [20.5, 20.0],
        "Giá trần": [21.0, 20.2],
        "Giá sàn": [19.0, 19.0],
        "Khối lượng giao dịch": [1000, 2000],
    })

    cleaned = clean_stock_data(df_raw)
    assert "Date" in cleaned.columns
    assert "Open" in cleaned.columns
    assert "Close" in cleaned.columns
    # Phải được sắp xếp theo Date tăng dần
    assert cleaned.iloc[0]["Date"] < cleaned.iloc[1]["Date"]


def test_load_local_data_exists():
    df = load_local_data("VIC")
    assert df is not None
    assert len(df) > 0
    assert "Close" in df.columns or "Giá đóng cửa" in df.columns
