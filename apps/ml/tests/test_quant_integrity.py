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
    frame["High"] = frame["Close"] + 1
    frame["Low"] = frame["Close"] - 1
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


def test_close_execution_benchmark_uses_same_entry_price():
    frame = market()
    frame["Close"] = 120.0
    frame["High"] = 120.0
    metrics, equity, trades = simulate_vietnam_trading(
        frame, np.array([2, 1, 1, 1, 1, 1]), initial_capital=100000,
        execution_price="close", fee_rate=0, tax_rate=0, slippage_rate=0,
    )
    assert trades.iloc[0].exec_price == 120
    assert metrics.final_equity == 100000
    assert equity.Benchmark_Equity.tolist() == [100000] * 6
    assert metrics.excess_return_pct == 0


def test_exact_cash_for_one_lot_executes_buy():
    _, equity, trades = simulate_vietnam_trading(
        market(3), np.array([2, 1, 1]), initial_capital=10000,
        fee_rate=0, tax_rate=0, slippage_rate=0, close_at_end=False,
    )
    assert len(trades) == 1
    assert trades.iloc[0].shares == 100
    assert equity.iloc[1].Cash == 0


@pytest.mark.parametrize("kwargs", [
    {"initial_capital": float("nan")}, {"initial_capital": -1},
    {"fee_rate": -0.1}, {"tax_rate": float("nan")},
    {"slippage_rate": 1.0}, {"lot_size": 0}, {"lot_size": 1.5},
    {"settlement_delay": 1.5}, {"stop_loss_pct": float("nan")},
])
def test_engine_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        simulate_vietnam_trading(market(), np.ones(6), **kwargs)


@pytest.mark.parametrize("column,value", [
    ("Open", 0), ("Close", float("nan")), ("High", 99),
    ("Low", 101), ("Volume", -1),
])
def test_engine_rejects_invalid_market_values(column, value):
    frame = market()
    frame.loc[2, column] = value
    with pytest.raises(ValueError):
        simulate_vietnam_trading(frame, np.ones(6))


@pytest.mark.parametrize("signals", [
    [1, 1, 1, 1, 1, 3], [1, 1, 1, 1, 1, 1.5], [[1]] * 6,
])
def test_engine_rejects_invalid_signals_even_on_last_bar(signals):
    with pytest.raises(ValueError):
        simulate_vietnam_trading(market(), np.array(signals))


@pytest.mark.parametrize("execution_price,sell_bar,next_buy", [("open", 4, 7), ("close", 3, 5)])
def test_sale_cash_waits_for_settlement_before_reinvestment(execution_price, sell_bar, next_buy):
    frame = market(10)
    signals = np.full(10, 2)
    signals[1:sell_bar] = 0
    _, equity, trades = simulate_vietnam_trading(
        frame, signals, initial_capital=10000, fee_rate=0, tax_rate=0,
        slippage_rate=0, execution_price=execution_price, close_at_end=False,
    )
    buys = trades[trades.order_type == "BUY"]
    assert buys.exec_date.tolist() == [frame.Date.iloc[j].strftime("%Y-%m-%d") for j in (1, next_buy)]
    assert equity.iloc[sell_bar].Cash == 0
    assert equity.iloc[sell_bar].Receivables == 10000
    if execution_price == "open":
        assert equity.iloc[sell_bar + 2].Cash == 10000
    else:
        assert equity.iloc[sell_bar + 2].Shares == 100
    np.testing.assert_allclose(equity.Total_Equity,
                               equity.Cash + equity.Receivables + equity.Position_Value)
    assert (equity.Cash >= 0).all()


def test_final_liquidation_is_receivable_not_available_cash():
    metrics, equity, trades = simulate_vietnam_trading(
        market(), np.array([2, 1, 1, 1, 1, 1]), initial_capital=10000,
        fee_rate=0, tax_rate=0, slippage_rate=0,
    )
    assert trades.iloc[-1].reason == "FINAL_LIQUIDATION"
    assert trades.iloc[-1].cash_after == 0
    assert equity.iloc[-1].Cash == 0
    assert equity.iloc[-1].Receivables == 10000
    assert metrics.final_equity == 10000


@pytest.mark.parametrize("probs", [
    [[0.2, 0.8]] * 6, [[0.2, 0.2, 0.2]] * 6,
    [[-0.1, 0.5, 0.6]] * 6, [[float("nan"), 0.5, 0.5]] * 6,
    [[0.1, 0.8, 0.1]] * 5,
])
def test_probability_matrix_is_validated(probs):
    from vn_stock.backtest import run_backtest
    with pytest.raises(ValueError):
        run_backtest(market(), probabilities=np.array(probs))


@pytest.mark.parametrize("threshold", [-0.1, 1.1, float("nan")])
def test_probability_threshold_is_validated(threshold):
    from vn_stock.backtest import run_backtest
    with pytest.raises(ValueError):
        run_backtest(market(), probabilities=np.tile([0.1, 0.8, 0.1], (6, 1)),
                     buy_prob_threshold=threshold)


def test_portfolio_does_not_hide_broken_symbol_or_fetch_market_data(monkeypatch):
    frame = market(10)
    monkeypatch.setattr("vn_stock.data_ingestion.load_local_data",
                        lambda symbol: frame.copy() if symbol == "VIC" else None)
    def forbid_fetch(*args, **kwargs):
        pytest.fail("Audit/backtest must not refresh market data implicitly")
    monkeypatch.setattr("vn_stock.data_ingestion.fetch_stock_data", forbid_fetch)
    with pytest.raises(ValueError, match="HPG"):
        run_portfolio_backtest(["VIC", "HPG"], model_type="none",
                               start_date="2026-01-05", end_date="2026-01-20")


@pytest.mark.parametrize("symbols,model_type", [([], "none"), (["VIC"], "typo")])
def test_portfolio_rejects_unintended_universe_or_model(symbols, model_type):
    with pytest.raises(ValueError):
        run_portfolio_backtest(symbols, model_type=model_type)


@pytest.mark.parametrize("rules", [{"use_pe": True}, {"use_pb": True}, {"growth_np_ttm": True}])
def test_fundamental_rules_require_historical_observations(rules):
    from vn_stock.backtest import evaluate_strategy_signals
    with pytest.raises(ValueError, match="historical|point-in-time"):
        evaluate_strategy_signals(prepare_backtest_df(market()), buy_rules=rules,
                                  symbol_meta={"pe": 12, "pb": 1, "growth_np_ttm": 10})


def test_fundamentals_use_available_historical_value_not_current_metadata():
    from vn_stock.backtest import evaluate_strategy_signals
    frame = prepare_backtest_df(market())
    frame["pe"] = [5, 20, 5, 20, 5, 20]
    frame["Fundamental_Available_At"] = frame.Date
    signals = evaluate_strategy_signals(frame, buy_rules={"use_pe": True, "max_pe": 10},
                                        symbol_meta={"pe": 100})
    assert signals.tolist() == [2, 1, 2, 1, 2, 1]
    frame.loc[0, "Fundamental_Available_At"] = frame.Date.iloc[1]
    with pytest.raises(ValueError, match="available|future"):
        evaluate_strategy_signals(frame, buy_rules={"use_pe": True})


@pytest.mark.parametrize("rules", [{"foreign_net_buy": True}, {"prop_net_buy": True}])
def test_order_flow_rules_do_not_invent_flows_from_volume(rules):
    from vn_stock.backtest import evaluate_strategy_signals
    with pytest.raises(ValueError, match="flow|historical"):
        evaluate_strategy_signals(prepare_backtest_df(market()), buy_rules=rules)


def test_presets_do_not_claim_unmeasured_performance_or_fabricate_recent_signals():
    from vn_stock.backtest import get_strategy_presets, get_recent_strategy_signals
    for preset in get_strategy_presets():
        for field in ("win_rate_pct", "cumulative_pnl_pct", "risk_reward_ratio", "copy_count"):
            assert preset[field] is None
    assert get_recent_strategy_signals() == []


def test_close_risk_decision_uses_previous_close_and_executes_next_session():
    frame = market(5)
    prices = [100, 100, 80, 70, 70]
    for column in ("Open", "High", "Low", "Close"):
        frame[column] = prices
    _, _, trades = simulate_vietnam_trading(
        frame, np.array([2, 1, 1, 1, 1]), initial_capital=10000,
        fee_rate=0, tax_rate=0, slippage_rate=0, settlement_delay=0,
        execution_price="close", stop_loss_pct=0.1, close_at_end=False,
    )
    sell = trades[trades.order_type == "SELL"].iloc[0]
    assert sell.signal_date == frame.Date.iloc[2].strftime("%Y-%m-%d")
    assert sell.exec_date == frame.Date.iloc[3].strftime("%Y-%m-%d")
    assert sell.exec_price == 70


def test_undefined_metrics_are_null_not_sentinels_or_zero():
    metrics = calculate_financial_metrics(pd.Series([100.0] * 4), 100, [], risk_free_rate=0)
    for name in ("sharpe_ratio", "sortino_ratio", "calmar_ratio", "profit_factor",
                 "win_rate_pct", "avg_trade_return_pct", "avg_holding_days",
                 "best_trade_return_pct", "worst_trade_return_pct", "var_95_pct", "cvar_95_pct"):
        assert getattr(metrics, name) is None, name
    one_point = calculate_financial_metrics(pd.Series([100.0]), 100, [])
    assert one_point.cagr_pct is None
    assert one_point.annualized_volatility_pct is None


@pytest.mark.parametrize("values", [[], [100, float("nan")], [100, float("inf")], [100, -1]])
def test_metrics_reject_invalid_equity(values):
    with pytest.raises(ValueError):
        calculate_financial_metrics(pd.Series(values, dtype=float), 100, [])


def test_metrics_include_initial_capital_before_first_loss():
    result = calculate_financial_metrics(pd.Series([90., 95.]), 100., [])
    assert result.total_return_pct == -5
    assert result.max_drawdown_pct == 10


def test_portfolio_returns_effective_configuration_and_data_fingerprint(monkeypatch):
    frame = market(10)
    monkeypatch.setattr("vn_stock.data_ingestion.load_local_data", lambda _: frame.copy())
    result = run_portfolio_backtest(["VIC"], model_type="none", initial_capital=100000,
                                   start_date="2026-01-05", end_date="2026-01-16")
    config = result["config"]
    assert config["initial_capital"] == 100000
    assert config["model_type"] == "none"
    assert config["evaluation_kind"] == "rule_based_historical_simulation"
    assert config["independent_oos"] is False
    assert len(config["data_fingerprints"]["VIC"]) == 64
    original_digest = config["data_fingerprints"]["VIC"]
    frame.loc[3, "Volume"] = 999
    changed = run_portfolio_backtest(["VIC"], model_type="none", initial_capital=100000,
                                    start_date="2026-01-05", end_date="2026-01-16")
    assert changed["config"]["data_fingerprints"]["VIC"] != original_digest


@pytest.mark.parametrize("rules", [
    {"use_ma": True, "ma_operator": "invalid"},
    {"use_ema": True, "ema_operator": "invalid"},
    {"use_macd": True, "macd_operator": "invalid"},
    {"use_price_cross": True, "price_cross_operator": "invalid"},
    {"use_price_increase": True, "price_t0_operator": "invalid"},
    {"use_ma": True, "ma_left": "MA 30"},
    {"market_condition": "uptrend"},
])
def test_strategy_rules_reject_unsupported_operators_indicators_and_market_regime(rules):
    from vn_stock.backtest import evaluate_strategy_signals
    with pytest.raises(ValueError):
        evaluate_strategy_signals(prepare_backtest_df(market()), buy_rules=rules)


def test_strategy_rules_reject_missing_rs_column():
    from vn_stock.backtest import evaluate_strategy_signals
    df = prepare_backtest_df(market()).drop(columns=["RS"])
    with pytest.raises(ValueError, match="RS"):
        evaluate_strategy_signals(df, buy_rules={"use_rs": True, "min_rs": 50})


def test_zero_volume_session_blocks_execution():
    frame = market(5)
    frame.loc[1, "Volume"] = 0
    _, _, trades = simulate_vietnam_trading(
        frame, np.array([2, 1, 1, 1, 1]), initial_capital=100_000,
        fee_rate=0, tax_rate=0, slippage_rate=0, settlement_delay=0, close_at_end=False,
    )
    assert trades.empty


def test_config_discloses_unverified_adjustments_and_pre_2022_settlement(monkeypatch):
    frame = market(10)
    frame["Date"] = pd.bdate_range("2022-08-01", periods=10)
    monkeypatch.setattr("vn_stock.data_ingestion.load_local_data", lambda _: frame.copy())
    result = run_portfolio_backtest(
        ["VIC"], model_type="none", initial_capital=100_000,
        start_date="2022-08-01", end_date="2022-08-12",
    )
    cfg = result["config"]
    assert cfg["price_adjustment_status"] == "unverified"
    assert cfg["corporate_actions_modeled"] is False
    assert cfg["dividend_modeled"] is False
    assert cfg["settlement_regime_effective_from"] == "2022-08-29"
    assert "2022-08-29" in cfg["settlement_regime_warning"]
    assert cfg["training_provenance"] == {}
    assert cfg["leakage_warning"] is None


def test_portfolio_reward_risk_ratio_edge_cases(monkeypatch):
    # Alternating up/down signals produce both winning and losing trades vs win-only
    dates = pd.bdate_range("2026-01-05", periods=15)
    closes = [100, 100, 110, 110, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95]
    frame = pd.DataFrame({
        "Date": dates,
        "Open": closes, "High": [c + 1 for c in closes],
        "Low": [c - 1 for c in closes], "Close": closes,
        "Volume": [1_000_000] * 15,
        "VNINDEX_Return_1d": [0.0] * 15,
    })
    monkeypatch.setattr("vn_stock.data_ingestion.load_local_data", lambda _: frame.copy())
    # Win-only (buy at 100, sell at 110): no losing trades -> reward_risk_ratio is None
    win_only = run_portfolio_backtest(
        ["VIC"], model_type="none", initial_capital=100_000_000,
        buy_rules={"use_stock_price": True, "min_stock_price": 99, "max_stock_price": 101},
        sell_rules={"use_stock_price": False},
        take_profit_pct=0.05,
        start_date="2026-01-05", end_date="2026-01-23",
    )
    assert win_only["aggregate_metrics"]["reward_risk_ratio"] is None
