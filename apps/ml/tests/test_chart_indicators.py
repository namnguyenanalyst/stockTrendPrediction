import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from vn_stock.chart_indicators import compute_chart_indicators
from vn_stock.backtest import prepare_backtest_df


def sample(n=250):
    close = np.arange(n, dtype=float) + 50
    return pd.DataFrame({'Date': pd.date_range('2020-01-01', periods=n), 'Close': close, 'High': close+1, 'Low': close-1, 'Volume': close*100})


def test_shared_backtest_and_no_future_leakage():
    data = sample()
    result = compute_chart_indicators(data)
    assert_frame_equal(result, prepare_backtest_df(data))
    assert_frame_equal(result.iloc[:100], compute_chart_indicators(data.iloc[:100]))
    assert result['SMA20'].iloc[-1] == data.Close.iloc[-20:].mean()
    assert result['MACD'].iloc[-1] == result['EMA12'].iloc[-1] - result['EMA26'].iloc[-1]


def test_short_history_and_input_unchanged():
    data = sample(1)
    before = data.copy()
    result = compute_chart_indicators(data)
    assert len(result) == 1
    assert_frame_equal(data, before)
