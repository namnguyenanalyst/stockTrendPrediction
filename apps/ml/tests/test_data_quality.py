import numpy as np
import pandas as pd

from vn_stock.data_quality import audit_panel, panel_fingerprint


def sample():
    return pd.DataFrame({"Date": pd.bdate_range("2026-01-05", periods=4), "Symbol": "VIC",
                         "Open": [100., 100., 50., 50.], "High": [101., 101., 51., 51.],
                         "Low": [99., 99., 49., 49.], "Close": [100., 100., 50., 50.],
                         "Volume": 100., "VNINDEX_Return_1d": 0.})


def test_jump_is_flagged_without_rewriting_source_or_certifying_adjustments():
    frame = sample()
    original = frame.copy(deep=True)
    result = audit_panel(frame)
    assert result["training_allowed"]
    assert not result["publication_ready"]
    assert result["large_jump_candidates"] == [{"symbol": "VIC", "date": "2026-01-07", "return": -0.5}]
    pd.testing.assert_frame_equal(frame, original)


def test_invalid_prices_and_duplicate_keys_block_training():
    frame = pd.concat([sample(), sample().iloc[[0]]], ignore_index=True)
    frame.loc[0, "Open"] = np.inf
    frame.loc[1, "Low"] = 200.
    result = audit_panel(frame)
    assert not result["training_allowed"]
    assert result["fatal_errors"]["duplicate_keys"] == 1
    assert result["fatal_errors"]["nonfinite_ohlcv_rows"] == 1
    assert result["fatal_errors"]["invalid_candle_bounds"] >= 1


def test_missing_observed_market_day_is_reported_and_legacy_columns_do_not_change_hash():
    frame = sample()
    reference = frame.Date.copy()
    frame = frame.drop(index=1)
    assert audit_panel(frame, reference)["symbols"]["VIC"]["missing_market_dates"] == ["2026-01-06"]
    enriched = frame.assign(Old_Indicator=np.nan)
    assert panel_fingerprint(enriched) == panel_fingerprint(frame.iloc[::-1])


def test_missing_core_columns_block_training():
    assert not audit_panel(sample().drop(columns="Volume"))["training_allowed"]


def test_malformed_close_is_reported_instead_of_crashing():
    frame = sample().astype({"Close": object})
    frame.loc[1, "Close"] = "bad-price"
    result = audit_panel(frame)
    assert not result["training_allowed"]
    assert result["fatal_errors"]["nonfinite_ohlcv_rows"] == 1
