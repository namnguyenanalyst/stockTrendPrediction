"""Regression cases with hand-calculated cash flows and time boundaries."""

import numpy as np
import pandas as pd
import pytest

from vn_stock.backtest import (
    calculate_financial_metrics, simulate_vietnam_trading, run_portfolio_backtest,
    prepare_backtest_df,
)


def market(count=6):
    return pd.DataFrame({
        "Date": pd.bdate_range("2026-01-05", periods=count),
        "Open": 100.0, "High": 100.0, "Low": 100.0, "Close": 100.0,
        "Volume": 1000000,
    })


@pytest.mark.parametrize("execution_price,expected_sell", [("open", 4), ("close", 3)])
def test_settlement_is_afternoon_not_open(execution_price, expected_sell):
    df = market()
    _, _, trades = simulate_vietnam_trading(
        df, np.array([2, 0, 0, 0, 0, 0]), execution_price=execution_price,
        close_at_end=False,
    )
    sells = trades[trades.order_type == "SELL"]
    assert len(sells) == 1
    assert sells.iloc[0].exec_date == df.Date.iloc[expected_sell].strftime("%Y-%m-%d")


def test_final_close_cannot_liquidate_an_unsettled_lot():
    _, equity, trades = simulate_vietnam_trading(market(3), np.array([2, 1, 1]))
    assert trades.order_type.tolist() == ["BUY"]
    assert equity.iloc[-1].Shares > 0


def test_final_liquidation_includes_sell_slippage_and_matches_benchmark():
    metrics, _, trades = simulate_vietnam_trading(
        market(), np.array([2, 1, 1, 1, 1, 1]), initial_capital=100000,
        slippage_rate=0.01,
    )
    sell = trades[trades.order_type == "SELL"].iloc[0]
    assert sell.exec_price == 99.0
    # 900 shares, buy cash 91036.35, net sale 88877.25.
    assert metrics.final_equity == pytest.approx(97840.90)
    assert metrics.total_return_pct == metrics.buy_and_hold_return_pct


def test_sortino_uses_all_periods_and_cagr_counts_return_intervals():
    equity = pd.Series([100.0, 110.0, 99.0, 108.9])
    metrics = calculate_financial_metrics(equity, 100.0, [], risk_free_rate=0)
    expected_sortino = np.sqrt(252) * (0.1 / 3) / np.sqrt(0.01 / 3)
    assert metrics.sortino_ratio == pytest.approx(expected_sortino, abs=0.0001)
    assert metrics.cagr_pct == pytest.approx(((1.089 ** 84) - 1) * 100, abs=0.01)


def test_signal_alignment_rejects_unsorted_market_rows():
    with pytest.raises(ValueError, match="sorted|tăng dần"):
        simulate_vietnam_trading(market().iloc[::-1], np.ones(6, dtype=int))


def test_strategy_features_do_not_change_when_future_rows_are_appended():
    frame = market(90)
    frame["Close"] = 100 + np.sin(np.arange(90)) * 10 + np.arange(90)
    prefix = prepare_backtest_df(frame.iloc[:75])
    complete = prepare_backtest_df(frame)
    np.testing.assert_allclose(prefix.RS, complete.RS.iloc[:75])


def test_portfolio_metrics_are_calculated_from_actual_equity_and_trade_log(monkeypatch):
    frame = market(30)
    frame["Close"] = frame["Open"] = 100 + np.sin(np.arange(30)) * 5
    monkeypatch.setattr("vn_stock.data_ingestion.load_local_data", lambda _: frame.copy())
    monkeypatch.setattr("vn_stock.backtest.evaluate_strategy_signals",
                        lambda *_, **__: np.array([2] + [1] * 29))
    result = run_portfolio_backtest(["VIC"], model_type="none", initial_capital=100000,
                                   price_unit="VND",
                                   start_date=str(frame.Date.min().date()),
                                   end_date=str(frame.Date.max().date()))
    aggregate = result["aggregate_metrics"]
    individual = result["individual_results"]["VIC"]["metrics"]
    for key in ["cagr_pct", "sortino_ratio", "sharpe_ratio", "var_95_pct",
                "total_fees_paid", "total_taxes_paid", "avg_holding_days", "profit_factor"]:
        assert aggregate[key] == individual[key], key


def test_ingestion_kvnd_prices_are_converted_before_lot_and_cash_calculations(monkeypatch):
    frame = market(6)
    frame[["Open", "High", "Low", "Close"]] = 50.0
    monkeypatch.setattr("vn_stock.data_ingestion.load_local_data", lambda _: frame.copy())
    monkeypatch.setattr("vn_stock.backtest.evaluate_strategy_signals",
                        lambda *_, **__: np.array([2, 1, 1, 1, 1, 1]))
    result = run_portfolio_backtest(["VIC"], model_type="none", initial_capital=10000000,
                                   start_date=str(frame.Date.min().date()),
                                   end_date=str(frame.Date.max().date()))
    trade = result["individual_results"]["VIC"]["trades"][0]
    assert trade["shares"] == 100
    assert trade["exec_price"] == 50025.0
