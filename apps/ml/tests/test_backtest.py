"""Kiểm thử cho module backtest."""

import numpy as np
from vn_stock.backtest import run_simple_backtest


def test_run_simple_backtest():
    # Giá tăng liên tục: dự báo tăng > 1.5% -> mua và có lãi
    prices = np.array([20.0, 21.0, 22.0, 23.0, 24.0, 25.0])
    predictions = prices * 1.03  # Dự báo luôn tăng 3%

    metrics = run_simple_backtest(
        prices=prices,
        predictions=predictions,
        initial_capital=10_000_000,
        buy_threshold=0.015,
        sell_threshold=-0.015,
    )

    assert metrics.total_return_pct > 0
    assert metrics.total_trades >= 1
    assert len(metrics.equity_curve) > 0
    assert metrics.final_equity > metrics.initial_capital
