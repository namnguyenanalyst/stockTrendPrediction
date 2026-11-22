import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler

from vn_stock.features import ALL_FEATURE_COLS, FEATURE_COLS, transform_model_features
from vn_stock.modeling.predict import prepare_inference_features
from vn_stock.backtest import backtest_symbol_oos


def test_transform_preserves_symbol_and_uses_training_statistics():
    train = pd.DataFrame(np.arange(52).reshape(4, 13), columns=FEATURE_COLS)
    scaler = StandardScaler().fit(train)
    frame = train.iloc[[0]].copy()
    frame["Symbol_Code"] = 25
    result = transform_model_features(frame, scaler)
    np.testing.assert_allclose(result[FEATURE_COLS], scaler.transform(train.iloc[[0]]))
    assert result.Symbol_Code.iloc[0] == 25
    assert frame.Symbol_Code.iloc[0] == 25


def test_transform_rejects_future_imputation_and_mismatched_scaler():
    frame = pd.DataFrame(1.0, index=range(2), columns=ALL_FEATURE_COLS)
    scaler = StandardScaler().fit(frame[FEATURE_COLS])
    frame.loc[0, FEATURE_COLS[0]] = np.nan
    with pytest.raises(ValueError, match="finite"):
        transform_model_features(frame, scaler)
    frame = frame.fillna(1.0)
    wrong = StandardScaler().fit(frame[FEATURE_COLS[::-1]])
    with pytest.raises(ValueError, match="order"):
        transform_model_features(frame, wrong)


def test_inference_never_consumes_cached_candles_after_target(monkeypatch):
    dates = pd.bdate_range("2024-01-01", periods=260)
    panel = pd.DataFrame({"Date": dates, "Symbol": "VIC", "Open": 50.,
                          "High": 51., "Low": 49., "Close": 50.,
                          "Volume": 1000., "VNINDEX_Return_1d": 0.})
    panel.loc[250:, "Close"] = 500.
    monkeypatch.setattr("vn_stock.modeling.predict.load_panel_dataset", lambda **_: panel)
    monkeypatch.setattr("vn_stock.modeling.predict.get_target_market_date",
                        lambda: dates[249].strftime("%Y-%m-%d"))
    features, price, date = prepare_inference_features("VIC")
    assert date == dates[249].strftime("%Y-%m-%d")
    assert price == 50.
    assert features.Date.max() == dates[249]


def test_validation_backtest_uses_persisted_scaler_not_refitted_statistics(monkeypatch):
    from types import SimpleNamespace
    dates = pd.bdate_range("2026-01-05", periods=8)
    frame = pd.DataFrame(10.0, index=range(8), columns=FEATURE_COLS)
    frame["Date"], frame["Symbol"], frame["Symbol_Code"] = dates, "VIC", 25
    frame["Open"] = frame["High"] = frame["Low"] = frame["Close"] = 50.0
    training = pd.DataFrame(0.0, index=range(3), columns=FEATURE_COLS)
    scaler = StandardScaler().fit(training)
    def predict(rows):
        # A scaler refitted on the constant validation features would produce zeros.
        np.testing.assert_allclose(rows[FEATURE_COLS], 10.0)
        return np.tile([0.1, 0.8, 0.1], (len(rows), 1))
    monkeypatch.setattr("vn_stock.data_ingestion.load_panel_dataset", lambda: frame)
    monkeypatch.setattr("vn_stock.features.compute_features_per_symbol", lambda *a, **kw: frame)
    monkeypatch.setattr("vn_stock.splitting_data.create_multi_day_labels", lambda *a, **kw: frame)
    monkeypatch.setattr("vn_stock.modeling.predict.load_prediction_snapshot",
                        lambda *a, **kw: (SimpleNamespace(predict=predict), scaler, {}))
    result = backtest_symbol_oos("VIC", "lightgbm")
    assert result.strategy_name == "AI_LIGHTGBM_VALIDATION"


def test_purge_counts_each_symbols_sessions_when_dates_are_sparse():
    from vn_stock.splitting_data import prepare_production_training_data
    dates=pd.bdate_range('2026-03-02',periods=20)
    dense=pd.DataFrame({'Date':dates,'Symbol':'VIC','Close':50.,'Label':1})
    sparse=pd.DataFrame({'Date':dates[[0,3,6,9,12,15,18,19]],'Symbol':'HPG','Close':30.,'Label':1})
    result=prepare_production_training_data(pd.concat([dense,sparse],ignore_index=True),val_buffer_days=4,
                                            feature_cols=['Close'],seq_length=2,purge_horizon=3)
    train=result['train'];tail=train[train.Symbol=='HPG'].sort_values('Date').tail(3)
    assert tail.Label.tolist()==[-1,-1,-1]
