"""SSI price jumps alone must not trigger assumed corporate-action rejection."""
from unittest.mock import patch
import numpy as np
import pandas as pd
from vn_stock.modeling.predict import prepare_inference_features
from vn_stock.data_ingestion import fetch_stock_data


def history():
    frame=pd.DataFrame({'Date':pd.bdate_range('2024-01-01',periods=300),'Symbol':'TCB',
                        'Open':30.,'High':31.,'Low':29.,'Close':30.,'Volume':1000000.,'VNINDEX_Return_1d':0.})
    frame.loc[290:,['Open','High','Low','Close']]=20.
    return frame


def test_source_price_jump_is_used_without_rejection_or_adjustment():
    frame=history()
    with patch('vn_stock.modeling.predict.get_target_market_date',return_value=str(frame.Date.max().date())):
        features,price,date=prepare_inference_features('TCB',raw_snapshot=frame)
    assert price==20.
    assert features.Close.iloc[-1]==20.
    assert frame.Close.iloc[0]==30.


def test_required_ssi_refresh_does_not_reject_or_rewrite_large_price_change():
    frame=history()
    with patch('vn_stock.data_ingestion.SSIFastConnectClient') as client:
        client.return_value.get_daily_ohlcv.return_value=frame
        result=fetch_stock_data('TCB',str(frame.Date.min().date()),str(frame.Date.max().date()),
                                require_fresh=True,save_to_raw=False)
    assert result.Close.iloc[0]==30.
    assert result.Close.iloc[-1]==20.


def test_training_does_not_apply_a_price_jump_quarantine(tmp_path):
    import pytest
    from vn_stock.modeling.train import train_production_model
    with patch('vn_stock.modeling.train.compute_features_per_symbol',side_effect=RuntimeError('feature computation reached')) as features:
        with pytest.raises(RuntimeError,match='feature computation reached'):
            train_production_model(symbols=['TCB'],raw_panel=history(),models_dir=tmp_path,save_artifacts=False)
    features.assert_called_once()
    assert not list(tmp_path.iterdir())
