"""Kiểm thử cho module data_ingestion."""

import pandas as pd
from vn_stock.data_ingestion import clean_stock_data, load_local_data


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


def test_clean_stock_data_proper_terminology():
    df_raw = pd.DataFrame({
        "Date": ["2024-01-02", "2024-01-01"],
        "Giá mở cửa": [20.0, 19.5],
        "Giá cao nhất": [21.0, 20.2],
        "Giá thấp nhất": [19.0, 19.0],
        "Giá đóng cửa": [20.5, 20.0],
        "Khối lượng": [1000, 2000],
    })

    cleaned = clean_stock_data(df_raw, symbol="VIC")
    assert "High" in cleaned.columns
    assert "Low" in cleaned.columns
    assert "Symbol" in cleaned.columns
    assert cleaned.iloc[0]["Symbol"] == "VIC"
    assert cleaned.iloc[0]["Date"] < cleaned.iloc[1]["Date"]


def test_build_and_load_panel_partitioned(tmp_path):
    from unittest.mock import patch
    from vn_stock.data_ingestion import build_panel_dataset, load_panel_dataset

    df_stock_vic = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
        "Symbol": ["VIC", "VIC"],
        "Open": [40.0, 41.0],
        "High": [41.0, 42.0],
        "Low": [39.5, 40.5],
        "Close": [40.5, 41.5],
        "Volume": [100000, 120000],
    })
    df_stock_hpg = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
        "Symbol": ["HPG", "HPG"],
        "Open": [25.0, 25.5],
        "High": [26.0, 26.5],
        "Low": [24.8, 25.2],
        "Close": [25.8, 26.2],
        "Volume": [200000, 220000],
    })
    df_vnindex = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
        "VNINDEX_Close": [1130.0, 1140.0],
        "VNINDEX_Return_1d": [0.01, 0.0088],
    })

    def mock_fetch_stock(symbol, **kwargs):
        return df_stock_vic if symbol == "VIC" else df_stock_hpg

    panel_dir = tmp_path / "panel"
    with patch("vn_stock.data_ingestion.fetch_stock_data", side_effect=mock_fetch_stock), \
         patch("vn_stock.data_ingestion.fetch_daily_index", return_value=df_vnindex), \
         patch("vn_stock.data_ingestion.PANEL_DATA_DIR", panel_dir):

        panel_df = build_panel_dataset(symbols=["VIC", "HPG"], save_to_interim=True)
        assert len(panel_df) == 4
        assert "VNINDEX_Return_1d" in panel_df.columns
        assert (panel_dir / "Symbol=VIC").exists()
        assert (panel_dir / "Symbol=HPG").exists()

        # Nạp có filter chỉ lấy VIC
        loaded_vic = load_panel_dataset(symbols=["VIC"], panel_dir=panel_dir)
        assert len(loaded_vic) == 2
        assert set(loaded_vic["Symbol"].unique()) == {"VIC"}

