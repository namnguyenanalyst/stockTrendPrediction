"""Kiểm thử cho module data_ingestion."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from vn_stock.data_ingestion import (
    InsufficientDataCoverageError,
    build_panel_dataset,
    check_cache_coverage,
    clean_stock_data,
    fetch_daily_index,
    fetch_stock_data,
    load_local_data,
    load_panel_dataset,
)


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


def test_load_local_data_exists(tmp_path):
    # Dùng dữ liệu tạm trong tmp_path, không phụ thuộc thư mục data/raw thật bị Git bỏ qua
    dummy_data = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
        "Open": [40.0, 41.0],
        "High": [41.0, 42.0],
        "Low": [39.5, 40.5],
        "Close": [40.5, 41.5],
        "Volume": [100000, 120000],
    })
    dummy_data.to_parquet(tmp_path / "VIC.parquet", index=False)

    df = load_local_data("VIC", data_dir=tmp_path)
    assert df is not None
    assert len(df) == 2
    assert "Close" in df.columns


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
    with (
        patch("vn_stock.data_ingestion.fetch_stock_data", side_effect=mock_fetch_stock),
        patch("vn_stock.data_ingestion.fetch_daily_index", return_value=df_vnindex),
        patch("vn_stock.data_ingestion.PANEL_DATA_DIR", panel_dir),
    ):
        panel_df = build_panel_dataset(
            symbols=["VIC", "HPG"],
            start_date="2024-01-02",
            end_date="2024-01-03",
            save_to_interim=True,
        )
        assert len(panel_df) == 4
        assert "VNINDEX_Return_1d" in panel_df.columns
        assert (panel_dir / "Symbol=VIC").exists()
        assert (panel_dir / "Symbol=HPG").exists()

        # Nạp có filter chỉ lấy VIC
        loaded_vic = load_panel_dataset(symbols=["VIC"], panel_dir=panel_dir)
        assert len(loaded_vic) == 2
        assert set(loaded_vic["Symbol"].unique()) == {"VIC"}
        # Đảm bảo Symbol sau khi load_panel_dataset có kiểu string (object), không phải Categorical
        assert pd.api.types.is_string_dtype(loaded_vic["Symbol"])


def test_cache_coverage_hit_and_miss():
    """Cache được dùng lại khi phạm vi ngày đủ, và bị bỏ qua khi file cũ không đủ phạm vi."""
    # 1. Cache cũ chỉ có từ 2023-01-03 đến 2026-09-10
    df_old_cache = pd.DataFrame({
        "Date": pd.to_datetime(["2023-01-03", "2026-09-10"]),
        "Close": [30.0, 40.0],
    })
    assert not check_cache_coverage(df_old_cache, start_date="2022-01-01", end_date="2026-09-11")

    # 2. Cache đầy đủ từ 2022-01-04 (sau nghỉ Tết) đến 2026-09-11
    df_full_cache = pd.DataFrame({
        "Date": pd.to_datetime(["2022-01-04", "2026-09-11"]),
        "Close": [30.0, 40.0],
    })
    assert check_cache_coverage(df_full_cache, start_date="2022-01-01", end_date="2026-09-11")

    # 3. Yêu cầu end_date cố định 2026-09-11 nhưng file chỉ tới 2026-09-10 -> MISS
    df_lacking_end = pd.DataFrame({
        "Date": pd.to_datetime(["2022-01-04", "2026-09-10"]),
        "Close": [30.0, 40.0],
    })
    assert not check_cache_coverage(df_lacking_end, start_date="2022-01-01", end_date="2026-09-11")


def test_atomic_download_failure_does_not_corrupt_existing_file(tmp_path):
    """Tải lỗi giữa chừng không ghi đè file cũ."""
    raw_file = tmp_path / "VIC.parquet"
    old_df = pd.DataFrame({
        "Date": pd.to_datetime(["2023-01-03", "2023-01-04"]),
        "Open": [50.0, 51.0],
        "High": [52.0, 53.0],
        "Low": [49.0, 50.0],
        "Close": [51.0, 52.0],
        "Volume": [1000, 2000],
    })
    old_df.to_parquet(raw_file, index=False)

    with (
        patch("vn_stock.data_ingestion.SSIFastConnectClient.get_daily_ohlcv", side_effect=RuntimeError("Mất kết nối API mạng")),
        patch("vn_stock.data_ingestion.RAW_DATA_DIR", tmp_path),
    ):
        _ = fetch_stock_data("VIC", start_date="2022-01-01", end_date="2026-09-11", force_refresh=True)

    preserved_df = pd.read_parquet(raw_file)
    assert len(preserved_df) == 2
    pd.testing.assert_frame_equal(preserved_df, old_df)

    tmp_files = list(tmp_path.glob("*.tmp*"))
    assert len(tmp_files) == 0


def test_build_panel_dataset_insufficient_coverage_guard():
    """Guard ném InsufficientDataCoverageError khi một mã không đủ độ phủ ngày yêu cầu."""
    df_vic = pd.DataFrame({
        "Date": pd.to_datetime(["2022-01-04", "2026-09-11"]),
        "Symbol": ["VIC", "VIC"],
        "Open": [50.0, 51.0],
        "High": [52.0, 53.0],
        "Low": [49.0, 50.0],
        "Close": [51.0, 52.0],
        "Volume": [1000, 2000],
    })

    # HPG thiếu ngày đầu (chỉ có từ 2024)
    df_hpg_short = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2026-09-11"]),
        "Symbol": ["HPG", "HPG"],
        "Open": [20.0, 21.0],
        "High": [22.0, 23.0],
        "Low": [19.0, 20.0],
        "Close": [21.0, 22.0],
        "Volume": [1000, 2000],
    })

    def mock_fetch(symbol, **kwargs):
        return df_vic if symbol == "VIC" else df_hpg_short

    with (
        patch("vn_stock.data_ingestion.fetch_stock_data", side_effect=mock_fetch),
        pytest.raises(InsufficientDataCoverageError, match="không bao phủ đủ dải ngày yêu cầu"),
    ):
        build_panel_dataset(
            symbols=["VIC", "HPG"],
            start_date="2022-01-01",
            end_date="2026-09-11",
            save_to_interim=False,
        )


def test_validate_downloaded_data_all_error_paths():
    """Kiểm tra toàn diện 7 kịch bản lỗi xác thực dữ liệu tải về trong validate_downloaded_data."""
    from vn_stock.data_ingestion import validate_downloaded_data

    # 1. Dữ liệu rỗng
    with pytest.raises(ValueError, match="rỗng"):
        validate_downloaded_data(pd.DataFrame(), expected_start="2024-01-01", symbol_name="VIC")

    # 2. Thiếu cột Date
    with pytest.raises(ValueError, match="thiếu cột 'Date'"):
        validate_downloaded_data(pd.DataFrame({"Close": [10.0]}), expected_start="2024-01-01", symbol_name="VIC")

    # 3. Ngày bị trùng lặp
    df_dup = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
        "Close": [10.0, 11.0],
    })
    with pytest.raises(ValueError, match="bị trùng lặp"):
        validate_downloaded_data(df_dup, expected_start="2024-01-01", symbol_name="VIC")

    # 4. Ngày không tăng dần đơn điệu
    df_unsorted = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-05", "2024-01-02"]),
        "Close": [10.0, 11.0],
    })
    with pytest.raises(ValueError, match="chưa được sắp xếp tăng dần"):
        validate_downloaded_data(df_unsorted, expected_start="2024-01-01", symbol_name="VIC")

    # 5. High < Low bất thường
    df_hl = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
        "High": [10.0, 8.0],
        "Low": [9.0, 9.0],  # 8.0 < 9.0
        "Close": [9.5, 8.5],
    })
    with pytest.raises(ValueError, match="High < Low"):
        validate_downloaded_data(df_hl, expected_start="2024-01-01", symbol_name="VIC")

    # 6. Close <= 0
    df_zero_c = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02"]),
        "Close": [0.0],
    })
    with pytest.raises(ValueError, match="Close <= 0"):
        validate_downloaded_data(df_zero_c, expected_start="2024-01-01", symbol_name="VIC")

    # 7. Thiếu ngày bắt đầu vượt quá dung sai 4 ngày
    df_short_start = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-15"]),
        "Close": [10.0],
    })
    with pytest.raises(ValueError, match="không phủ đủ ngày bắt đầu"):
        validate_downloaded_data(df_short_start, expected_start="2024-01-01", symbol_name="VIC")

    # 8. Thiếu ngày kết thúc cố định vượt quá dung sai 4 ngày
    df_short_end = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02"]),
        "Close": [10.0],
    })
    with pytest.raises(ValueError, match="không phủ đủ ngày kết thúc cố định"):
        validate_downloaded_data(df_short_end, expected_start="2024-01-01", expected_end="2024-01-20", symbol_name="VIC")


def test_atomic_save_parquet(tmp_path):
    """Kiểm tra hàm _atomic_save_parquet ghi file nguyên tử và ghi đè an toàn."""
    from vn_stock.data_ingestion import _atomic_save_parquet

    target_file = tmp_path / "test_stock.parquet"
    df1 = pd.DataFrame({"Date": pd.to_datetime(["2024-01-02"]), "Close": [10.0]})
    _atomic_save_parquet(df1, target_file)
    assert target_file.exists()
    assert len(pd.read_parquet(target_file)) == 1

    # Ghi đè an toàn
    df2 = pd.DataFrame({"Date": pd.to_datetime(["2024-01-02", "2024-01-03"]), "Close": [10.0, 11.0]})
    _atomic_save_parquet(df2, target_file)
    assert len(pd.read_parquet(target_file)) == 2


def test_sync_latest_market_data():
    """Kiểm tra tiến trình đồng bộ dữ liệu thị trường đa mã sync_latest_market_data."""
    from vn_stock.data_ingestion import sync_latest_market_data

    with (
        patch("vn_stock.data_ingestion.fetch_daily_index") as mock_vni,
        patch("vn_stock.data_ingestion.fetch_stock_data") as mock_sym,
        patch("vn_stock.data_ingestion.build_panel_dataset") as mock_panel,
    ):
        mock_vni.return_value = pd.DataFrame()
        mock_sym.return_value = pd.DataFrame()
        mock_panel.return_value = pd.DataFrame()

        res = sync_latest_market_data(symbols=["VIC", "HPG"], force=False)
        assert res["status"] == "success"
        assert "VNINDEX" in res["synced_symbols"]
        assert "VIC" in res["synced_symbols"]
        assert "HPG" in res["synced_symbols"]
        assert len(res["errors"]) == 0


def test_fetch_daily_index_network_and_cache(tmp_path):
    """Kiểm tra fetch_daily_index khi force_refresh=True và lưu parquet."""
    from unittest.mock import MagicMock

    dates = pd.date_range("2024-01-01", "2024-01-15", freq="D")
    mock_idx = pd.DataFrame({
        "Date": dates,
        "VNINDEX_Close": np.linspace(1100.0, 1150.0, len(dates)),
    })

    with (
        patch("vn_stock.data_ingestion.RAW_DATA_DIR", tmp_path),
        patch("vn_stock.data_ingestion.SSIFastConnectClient") as mock_client_cls,
    ):
        mock_client = MagicMock()
        mock_client.get_daily_index.return_value = mock_idx
        mock_client_cls.return_value = mock_client

        res = fetch_daily_index(
            index_id="VNINDEX",
            start_date="2024-01-01",
            end_date="2024-01-15",
            force_refresh=True,
            save_to_raw=True,
        )

        assert len(res) == len(dates)
        assert "VNINDEX_Return_1d" in res.columns
        assert (tmp_path / "VNINDEX.parquet").exists()

        # Lần 2: Đọc từ cache với force_refresh=False
        res_cached = fetch_daily_index(
            index_id="VNINDEX",
            start_date="2024-01-01",
            end_date="2024-01-15",
            force_refresh=False,
            save_to_raw=False,
        )
        assert len(res_cached) == len(dates)
        # Không được gọi API lần 2 vì cache đã bao phủ đủ 100%
        assert mock_client.get_daily_index.call_count == 1


def test_fetch_stock_data_force_and_cache(tmp_path):
    """Kiểm tra fetch_stock_data khi force_refresh=True và đọc lại cache."""
    from unittest.mock import MagicMock

    dates = pd.date_range("2024-01-01", "2024-01-15", freq="D")
    mock_stock = pd.DataFrame({
        "Date": dates,
        "Symbol": ["TESTSYM"] * len(dates),
        "Open": [50.0] * len(dates),
        "High": [52.0] * len(dates),
        "Low": [49.0] * len(dates),
        "Close": [51.0] * len(dates),
        "Volume": [100000] * len(dates),
    })

    with (
        patch("vn_stock.data_ingestion.RAW_DATA_DIR", tmp_path),
        patch("vn_stock.data_ingestion.load_local_data", return_value=None),
        patch("vn_stock.data_ingestion.SSIFastConnectClient") as mock_client_cls,
    ):
        mock_client = MagicMock()
        mock_client.get_daily_ohlcv.return_value = mock_stock
        mock_client_cls.return_value = mock_client

        res = fetch_stock_data(
            symbol="TESTSYM",
            start_date="2024-01-01",
            end_date="2024-01-15",
            force_refresh=True,
            save_to_raw=True,
        )
        assert len(res) == len(dates)
        assert (tmp_path / "TESTSYM.parquet").exists()






