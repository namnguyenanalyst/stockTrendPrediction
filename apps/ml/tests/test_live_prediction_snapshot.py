"""A live prediction must consume the fetched snapshot without touching shared caches."""
from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest


def stock_history():
    dates = pd.bdate_range('2024-01-01', periods=300)
    close = 30. + np.arange(300) * .01
    return pd.DataFrame({'Date':dates,'Open':close,'High':close+1,'Low':close-1,
                         'Close':close,'Volume':1000000.,'Symbol':'VIC'})


def test_live_snapshot_fetches_stock_and_market_without_writes():
    from vn_stock.data_ingestion import fetch_live_prediction_panel
    stock = stock_history()
    market = pd.DataFrame({'Date':stock.Date,'VNINDEX_Close':1000.+np.arange(300)})
    target = str(stock.Date.max().date())
    with patch('vn_stock.data_ingestion.fetch_stock_data',return_value=stock) as fetch, \
         patch('vn_stock.data_ingestion.fetch_daily_index',return_value=market) as index:
        panel = fetch_live_prediction_panel('VIC', target)
    assert fetch.call_args.kwargs['save_to_raw'] is False
    assert fetch.call_args.kwargs['require_fresh'] is True
    assert index.call_args.kwargs['save_to_raw'] is False
    assert index.call_args.kwargs['force_refresh'] is True
    assert fetch.call_args.kwargs['end_date'] == index.call_args.kwargs['end_date'] == target
    assert panel.Close.iloc[-1] == stock.Close.iloc[-1]
    assert panel.VNINDEX_Return_1d.iloc[-1] == pytest.approx(market.VNINDEX_Close.pct_change().iloc[-1])


@pytest.mark.parametrize('fault',['missing_day','duplicate_day','nonfinite_close','offline'])
def test_live_snapshot_never_substitutes_missing_market_data(fault):
    from vn_stock.data_ingestion import fetch_live_prediction_panel
    stock = stock_history()
    market = pd.DataFrame({'Date':stock.Date,'VNINDEX_Close':1000.})
    if fault == 'missing_day': market = market.iloc[:-1]
    if fault == 'duplicate_day': market = pd.concat([market, market.tail(1)])
    if fault == 'nonfinite_close': market.loc[290,'VNINDEX_Close'] = np.nan
    kwargs = {'side_effect': OSError('SSI offline')} if fault == 'offline' else {'return_value': market}
    with patch('vn_stock.data_ingestion.fetch_stock_data',return_value=stock), \
         patch('vn_stock.data_ingestion.fetch_daily_index',**kwargs):
        with pytest.raises((ValueError, RuntimeError, OSError)):
            fetch_live_prediction_panel('VIC', str(stock.Date.max().date()))


def test_explicit_inference_snapshot_does_not_read_old_panel_or_fetch_again():
    from vn_stock.modeling.predict import prepare_inference_features
    stock = stock_history().assign(VNINDEX_Return_1d=0.)
    original = stock.copy(deep=True)
    with patch('vn_stock.modeling.predict.get_target_market_date',return_value=str(stock.Date.max().date())), \
         patch('vn_stock.modeling.predict.load_panel_dataset',side_effect=AssertionError('old panel read')), \
         patch('vn_stock.modeling.predict.fetch_stock_data',side_effect=AssertionError('second fetch')):
        frame, price, date = prepare_inference_features('VIC', raw_snapshot=stock)
    assert price == stock.Close.iloc[-1]
    assert date == str(stock.Date.max().date())
    assert len(frame) >= 20
    pd.testing.assert_frame_equal(stock, original)


def test_explicit_snapshot_for_wrong_symbol_is_rejected_without_fallback():
    from vn_stock.modeling.predict import prepare_inference_features
    with pytest.raises(ValueError,match='symbol'):
        prepare_inference_features('HPG',raw_snapshot=stock_history().assign(VNINDEX_Return_1d=0.))


def test_bounded_market_fetch_preserves_full_history_feature_window():
    from vn_stock.data_ingestion import fetch_live_prediction_panel
    from vn_stock.features import compute_features_per_symbol, FEATURE_COLS
    stock = stock_history()
    market = pd.DataFrame({'Date':stock.Date, 'VNINDEX_Close':1000.+np.arange(300)})
    full = stock.assign(VNINDEX_Return_1d=market.VNINDEX_Close.pct_change())
    with patch('vn_stock.data_ingestion.fetch_stock_data',return_value=stock), \
         patch('vn_stock.data_ingestion.fetch_daily_index',return_value=market) as fetch:
        bounded = fetch_live_prediction_panel('VIC',str(stock.Date.max().date()))
    assert fetch.call_args.kwargs['start_date'] == str(stock.Date.iloc[-21].date())
    assert len(bounded) == len(stock)
    assert bounded.VNINDEX_Return_1d.notna().sum() == 20
    expected = compute_features_per_symbol(full).tail(20)[FEATURE_COLS].reset_index(drop=True)
    actual = compute_features_per_symbol(bounded).tail(20)[FEATURE_COLS].reset_index(drop=True)
    pd.testing.assert_frame_equal(actual, expected)
