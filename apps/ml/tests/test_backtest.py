"""Kiểm thử tự động toàn diện cho module Backtesting Engine (Phase 4).

Kiểm tra:
1. Tính tương thích ngược của run_simple_backtest.
2. Logic khớp lệnh T+2 nghiêm ngặt (chống bán khi cổ phiếu chưa về tài khoản).
3. Khấu trừ chính xác thuế phí thực tế (0.15% mua, 0.15% bán + 0.10% thuế).
4. Khớp lệnh theo lô chẵn 100 cổ phiếu và bảo toàn số dư tiền mặt.
5. Tính toán chính xác các chỉ số tài chính: ROI, CAGR, Sharpe, Sortino, MDD, Win Rate, Profit Factor.
6. Chiến lược Buy & Hold, Random Strategy Baseline và Monte Carlo.
7. Đầu ra BacktestResult.to_dict() phục vụ REST API endpoint /api/backtest/run.
"""

import numpy as np
import pandas as pd
import pytest

from vn_stock.backtest import (
    PositionLot,
    TradeRecord,
    backtest_all_symbols,
    backtest_symbol_oos,
    calculate_financial_metrics,
    evaluate_strategy_signals,
    get_recent_strategy_signals,
    get_strategy_presets,
    prepare_backtest_df,
    run_backtest,
    run_buy_and_hold,
    run_monte_carlo_random_test,
    run_portfolio_backtest,
    run_random_baseline,
    run_simple_backtest,
    simulate_vietnam_trading,
)


def _create_sample_market_df(n_bars: int = 10, start_price: float = 100.0) -> pd.DataFrame:
    """Tạo DataFrame thị trường giả lập cho kiểm thử."""
    dates = pd.date_range("2026-01-01", periods=n_bars, freq="B")
    prices = [start_price + i * 2.0 for i in range(n_bars)]
    return pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": [p + 1.0 for p in prices],
        "Low": [p - 1.0 for p in prices],
        "Close": prices,
        "Volume": [1_000_000] * n_bars,
    })


def test_run_simple_backtest_backward_compatibility():
    """Kiểm tra tương thích ngược của run_simple_backtest với mã cũ."""
    prices = np.array([20.0, 21.0, 22.0, 23.0, 24.0, 25.0])
    predictions = prices * 1.03

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


def test_t2_settlement_restriction():
    """
    Kiểm định quy chế T+2:
    - Ngày 0: Phát tín hiệu Mua (sig=2) -> Ngày 1: Khớp Mua tại Open_1.
    - Ngày 1: Phát tín hiệu Bán (sig=0) -> Ngày 2: Đòi khớp Bán.
      Tuy nhiên, hàng mua tại ngày 1 phải đến ngày 1 + 2 = ngày 3 mới về!
      Do đó, tại ngày 2 lệnh Bán BẮT BUỘC BỊ TỪ CHỐI, không được khớp.
    - Ngày 2: Phát tín hiệu Bán (sig=0) -> Ngày 3: Hàng đã về (settled_idx=3 <= 3), lệnh Bán ĐƯỢC PHÉP KHỚP.
    """
    df = _create_sample_market_df(n_bars=6, start_price=50.0)
    # Tín hiệu: [Mua, Bán (quá sớm), Bán (hợp lệ), Giữ, Giữ, Giữ]
    signals = np.array([2, 0, 0, 1, 1, 1])

    metrics, eq_df, trades_df = simulate_vietnam_trading(
        df=df,
        signals=signals,
        symbol="VIC",
        initial_capital=100_000_000,
        settlement_delay=2,
        close_at_end=False,  # Không đóng vị thế phiên cuối để kiểm tra lệnh bán tự nhiên
    )

    # Phải có đúng 1 lệnh BUY và 1 lệnh SELL
    buy_trades = trades_df[trades_df["order_type"] == "BUY"]
    sell_trades = trades_df[trades_df["order_type"] == "SELL"]

    assert len(buy_trades) == 1
    assert len(sell_trades) == 1

    # Lệnh Mua khớp tại bar 1
    assert buy_trades.iloc[0]["exec_date"] == df.iloc[1]["Date"].strftime("%Y-%m-%d")
    # Lệnh Bán chỉ được khớp tại bar 3 (không phải bar 2 vì T+2!)
    assert sell_trades.iloc[0]["exec_date"] == df.iloc[3]["Date"].strftime("%Y-%m-%d")
    assert sell_trades.iloc[0]["holding_days"] == 2.0


def test_transaction_fee_and_tax_deductions():
    """
    Kiểm tra tính chính xác của công thức trừ phí mua 0.15%, phí bán 0.15% và thuế bán 0.10%.
    """
    df = _create_sample_market_df(n_bars=6, start_price=100.0)
    # Ngày 0: Mua, Ngày 1: Giữ, Ngày 2: Bán (khớp ngày 3, thỏa mãn T+2)
    signals = np.array([2, 1, 0, 1, 1, 1])

    metrics, eq_df, trades_df = simulate_vietnam_trading(
        df=df,
        signals=signals,
        initial_capital=10_000_000,
        fee_rate=0.0015,
        tax_rate=0.0010,
        slippage_rate=0.0,
        lot_size=100,
        close_at_end=False,
    )

    buy_trade = trades_df[trades_df["order_type"] == "BUY"].iloc[0]
    sell_trade = trades_df[trades_df["order_type"] == "SELL"].iloc[0]

    # Kiểm tra lệnh Mua
    expected_buy_gross = buy_trade["shares"] * buy_trade["exec_price"]
    expected_buy_fee = expected_buy_gross * 0.0015
    assert pytest.approx(buy_trade["gross_value"], 0.01) == expected_buy_gross
    assert pytest.approx(buy_trade["fee"], 0.01) == expected_buy_fee
    assert buy_trade["tax"] == 0.0
    assert pytest.approx(buy_trade["net_cash_flow"], 0.01) == -(expected_buy_gross + expected_buy_fee)

    # Kiểm tra lệnh Bán
    expected_sell_gross = sell_trade["shares"] * sell_trade["exec_price"]
    expected_sell_fee = expected_sell_gross * 0.0015
    expected_sell_tax = expected_sell_gross * 0.0010
    assert pytest.approx(sell_trade["gross_value"], 0.01) == expected_sell_gross
    assert pytest.approx(sell_trade["fee"], 0.01) == expected_sell_fee
    assert pytest.approx(sell_trade["tax"], 0.01) == expected_sell_tax
    assert pytest.approx(sell_trade["net_cash_flow"], 0.01) == (
        expected_sell_gross - expected_sell_fee - expected_sell_tax
    )

    # Kiểm tra quy cách lô chẵn 100
    assert buy_trade["shares"] % 100 == 0
    assert sell_trade["shares"] % 100 == 0


def test_financial_metrics_calculation_accuracy():
    """Kiểm tra độ chính xác của hàm tính chỉ số tài chính (Sharpe, Sortino, MDD, Win Rate, Profit Factor)."""
    # Tạo đường vốn giả lập: 100 -> 105 -> 102 -> 110 -> 108 -> 115
    equity = pd.Series([100.0, 105.0, 102.0, 110.0, 108.0, 115.0])
    trades = [
        TradeRecord(
            trade_id=1, symbol="VIC", order_type="SELL", signal_date="2026-01-01",
            exec_date="2026-01-03", exec_price=105.0, shares=100, gross_value=10500.0,
            fee=15.0, tax=10.0, net_cash_flow=10475.0, cash_after=10475.0,
            realized_pnl=475.0, realized_return_pct=4.75, holding_days=2.0, reason="SIGNAL_SELL"
        ),
        TradeRecord(
            trade_id=2, symbol="VIC", order_type="SELL", signal_date="2026-01-04",
            exec_date="2026-01-06", exec_price=98.0, shares=100, gross_value=9800.0,
            fee=15.0, tax=10.0, net_cash_flow=9775.0, cash_after=9775.0,
            realized_pnl=-225.0, realized_return_pct=-2.25, holding_days=2.0, reason="SIGNAL_SELL"
        ),
    ]

    metrics = calculate_financial_metrics(
        equity_series=equity,
        initial_capital=100.0,
        trades=trades,
        risk_free_rate=0.04,
        buy_and_hold_return_pct=10.0,
    )

    assert metrics.total_return_pct == 15.0
    assert metrics.excess_return_pct == 5.0
    assert metrics.total_trades == 2
    assert metrics.winning_trades == 1
    assert metrics.losing_trades == 1
    assert metrics.win_rate_pct == 50.0
    # Profit factor = 475.0 / 225.0 ≈ 2.1111
    assert pytest.approx(metrics.profit_factor, 0.01) == (475.0 / 225.0)
    assert metrics.max_drawdown_pct > 0.0
    assert metrics.sharpe_ratio > 0.0


def test_run_buy_and_hold_strategy():
    """Kiểm tra chiến lược đối chứng Mua & Nắm giữ (Buy & Hold)."""
    df = _create_sample_market_df(n_bars=8, start_price=50.0)
    res = run_buy_and_hold(df, symbol="HPG", initial_capital=50_000_000)

    assert res.strategy_name == "Buy_and_Hold"
    assert res.metrics.total_trades >= 1
    assert res.metrics.total_return_pct == res.metrics.buy_and_hold_return_pct
    assert res.metrics.excess_return_pct == 0.0
    assert len(res.equity_df) == len(df)


def test_run_backtest_with_probability_matrix():
    """Kiểm tra khả năng nhận ma trận xác suất 3 lớp và áp dụng ngưỡng xác suất."""
    df = _create_sample_market_df(n_bars=5, start_price=100.0)
    # Xác suất: [P(Giảm), P(Đi ngang), P(Tăng)]
    probs = np.array([
        [0.1, 0.3, 0.6],  # Tăng >= 0.40 -> Tín hiệu 2 (Mua)
        [0.1, 0.7, 0.2],  # Đi ngang -> Tín hiệu 1 (Giữ)
        [0.6, 0.3, 0.1],  # Giảm >= 0.40 -> Tín hiệu 0 (Bán)
        [0.2, 0.6, 0.2],  # Đi ngang -> Tín hiệu 1 (Giữ)
        [0.1, 0.8, 0.1],  # Đi ngang -> Tín hiệu 1 (Giữ)
    ])

    res = run_backtest(
        df=df,
        probabilities=probs,
        buy_prob_threshold=0.40,
        sell_prob_threshold=0.40,
        symbol="FPT",
        initial_capital=50_000_000,
    )

    assert len(res.trades_df) >= 2
    assert "SIGNAL_BUY" in res.trades_df["reason"].values


def test_run_monte_carlo_random_baseline():
    """Kiểm tra chạy kiểm định Monte Carlo đối chứng ngẫu nhiên."""
    df = _create_sample_market_df(n_bars=8, start_price=50.0)
    signals = np.array([2, 1, 0, 1, 1, 1, 1, 1])
    ai_res = run_backtest(df=df, signals=signals, symbol="VIC", initial_capital=20_000_000)

    mc_res = run_monte_carlo_random_test(
        df=df,
        symbol="VIC",
        ai_result=ai_res,
        n_simulations=10,
        seed=42,
    )

    assert mc_res["n_simulations"] == 10
    assert "roi_stats" in mc_res
    assert "sharpe_stats" in mc_res
    assert "mdd_stats" in mc_res
    assert "ai_comparison" in mc_res
    assert "p_value_sharpe" in mc_res["ai_comparison"]
    assert 0.0 <= mc_res["ai_comparison"]["p_value_sharpe"] <= 1.0


def test_backtest_result_to_dict():
    """Kiểm tra hàm to_dict() xuất cấu trúc JSON chuẩn cho REST API."""
    df = _create_sample_market_df(n_bars=5, start_price=60.0)
    signals = np.array([2, 1, 0, 1, 1])
    res = run_backtest(df=df, signals=signals, symbol="MWG", initial_capital=30_000_000)

    d = res.to_dict()
    assert d["symbol"] == "MWG"
    assert "metrics" in d
    assert "equity_curve_summary" in d
    assert "dates" in d["equity_curve_summary"]
    assert "total_equity" in d["equity_curve_summary"]
    assert isinstance(d["metrics"]["total_return_pct"], float)


def test_dnse_risk_management_stop_loss():
    """Kiểm tra cơ chế Cắt lỗ tự động (Stop Loss): bán ngay khi giảm >= stop_loss_pct sau T+2."""
    from vn_stock.backtest import get_strategy_presets, get_recent_strategy_signals
    # Giá: ngày 0: 100, ngày 1: 100 (mua), ngày 2: 95, ngày 3: 85 (giảm 15% -> kích hoạt Stop Loss 10%), ngày 4: 80
    dates = pd.date_range("2026-01-01", periods=5, freq="B")
    df = pd.DataFrame({
        "Date": dates,
        "Open": [100.0, 100.0, 95.0, 85.0, 80.0],
        "High": [101.0, 101.0, 96.0, 86.0, 81.0],
        "Low": [99.0, 99.0, 94.0, 84.0, 79.0],
        "Close": [100.0, 100.0, 95.0, 85.0, 80.0],
        "Volume": [1_000_000] * 5,
    })
    # Tín hiệu AI luôn là HOLD (1) để kiểm tra việc Stop Loss tự động kích hoạt bán
    signals = np.array([2, 1, 1, 1, 1])

    res = run_backtest(
        df=df,
        signals=signals,
        symbol="HPG",
        initial_capital=50_000_000,
        stop_loss_pct=0.10,  # Cắt lỗ 10%
        close_at_end=False,
    )

    sell_trades = res.trades_df[res.trades_df["order_type"] == "SELL"]
    assert len(sell_trades) == 1
    assert sell_trades.iloc[0]["reason"] == "STOP_LOSS"
    assert sell_trades.iloc[0]["exec_price"] < 100.0


def test_dnse_presets_and_signals():
    """Kiểm tra hàm get_strategy_presets và get_recent_strategy_signals."""
    from vn_stock.backtest import get_strategy_presets, get_recent_strategy_signals

    presets = get_strategy_presets()
    assert len(presets) == 8
    assert presets[0]["id"] == "preset_ema20_breakout"
    assert "win_rate_pct" in presets[0]
    assert "take_profit_pct" in presets[0]

    signals = get_recent_strategy_signals()
    assert len(signals) >= 3
    assert signals[0]["action"] in ["BUY", "SELL", "HOLD"]


def test_evaluate_strategy_signals():
    """Kiểm tra hàm đánh giá bộ điều kiện Mua / Bán chuẩn DNSE."""
    from vn_stock.backtest import evaluate_strategy_signals, prepare_backtest_df

    dates = pd.date_range("2026-01-01", periods=30, freq="B")
    prices = [50.0 + i * 0.5 for i in range(30)]
    df = pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": [p + 1.0 for p in prices],
        "Low": [p - 1.0 for p in prices],
        "Close": prices,
        "Volume": [2_000_000] * 30,
    })
    df_prepared = prepare_backtest_df(df)

    buy_rules = {"use_ma": True, "use_rsi": True, "rsi_threshold": 50.0}
    sell_rules = {"use_rsi": True, "rsi_sell_threshold": 70.0}

    signals = evaluate_strategy_signals(df_prepared, buy_rules=buy_rules, sell_rules=sell_rules)
    assert len(signals) == 30
    assert set(signals).issubset({0, 1, 2})


def test_evaluate_strategy_signals_and_or_logic():
    """Kiểm tra sự khác biệt giữa toán tử logic AND và OR khi đánh giá điều kiện Mua."""
    from vn_stock.backtest import evaluate_strategy_signals, prepare_backtest_df

    dates = pd.date_range("2026-01-01", periods=20, freq="B")
    prices = [50.0 + i * 0.2 for i in range(20)]
    df = pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": [p + 0.5 for p in prices],
        "Low": [p - 0.5 for p in prices],
        "Close": prices,
        "Volume": [1_000_000] * 20,
    })
    df_prepared = prepare_backtest_df(df)

    # 1. Logic AND: Cả use_ma và use_rsi (ngưỡng cực thấp 10.0 không bao giờ đạt) -> Không có tín hiệu MUA
    buy_rules_and = {
        "condition_logic": "AND",
        "use_ma": True,
        "use_rsi": True,
        "rsi_threshold": 10.0,
    }
    signals_and = evaluate_strategy_signals(df_prepared, buy_rules=buy_rules_and)
    assert not any(s == 2 for s in signals_and)

    # 2. Logic OR: Chỉ cần use_ma thỏa mãn (Close > SMA20) là sinh tín hiệu MUA
    buy_rules_or = {
        "condition_logic": "OR",
        "use_ma": True,
        "use_rsi": True,
        "rsi_threshold": 10.0,
    }
    signals_or = evaluate_strategy_signals(df_prepared, buy_rules=buy_rules_or)
    assert any(s == 2 for s in signals_or)


def test_run_portfolio_backtest():
    """Kiểm tra chạy Backtest danh mục đa mã và các chỉ số Deal thực chiến (Max Gain, Max Loss, R:R)."""
    from vn_stock.backtest import run_portfolio_backtest

    res = run_portfolio_backtest(
        symbols=["VIC", "HPG"],
        start_date="2024-01-01",
        end_date="2024-06-30",
        initial_capital=100_000_000,
        buy_rules={"use_ma": True, "condition_logic": "AND"},
        sell_rules={"take_profit_pct": 0.15, "stop_loss_pct": 0.07, "condition_logic": "OR"},
    )

    assert "aggregate_metrics" in res
    assert "portfolio_equity_curve" in res
    assert "symbols_breakdown" in res
    assert "individual_results" in res
    for sym, ind in res["individual_results"].items():
        assert "equity_curve" in ind
        if len(ind["equity_curve"]) > 0:
            first_pt = ind["equity_curve"][0]
            assert "date" in first_pt
            assert "total_equity" in first_pt
            assert "benchmark_equity" in first_pt
            assert "drawdown_pct" in first_pt
            assert "daily_return" in first_pt

    agg = res["aggregate_metrics"]
    assert agg["initial_capital"] == 100_000_000
    assert len(res["symbols_breakdown"]) >= 1
    assert len(res["portfolio_equity_curve"]) > 0
    assert "max_gain_pct" in agg
    assert "max_loss_pct" in agg
    assert "reward_risk_ratio" in agg
    assert isinstance(agg["max_gain_pct"], float)
    assert isinstance(agg["max_loss_pct"], float)


def test_fine_tuned_parameters_impact():
    """Kiểm tra các thông số tinh chỉnh (RSI min/max, MA cross, Volume spike) thực sự thay đổi kết quả kiểm thử."""
    from vn_stock.backtest import prepare_backtest_df, evaluate_strategy_signals

    df = _create_sample_market_df(n_bars=30, start_price=30.0)
    df_prepared = prepare_backtest_df(df)

    # 1. Tinh chỉnh khoảng RSI: [0, 40] vs [40, 100]
    rules_rsi_low = {
        "use_rsi": True,
        "rsi_min": 0.0,
        "rsi_max": 40.0,
    }
    rules_rsi_high = {
        "use_rsi": True,
        "rsi_min": 40.0,
        "rsi_max": 100.0,
    }
    sig_low = evaluate_strategy_signals(df_prepared, buy_rules=rules_rsi_low)
    sig_high = evaluate_strategy_signals(df_prepared, buy_rules=rules_rsi_high)
    assert np.sum(sig_high == 2) >= np.sum(sig_low == 2)

    # 2. Tinh chỉnh MA operator: "Cắt lên" vs "Nằm trên"
    rules_ma_cross = {
        "use_ma": True,
        "ma_left": "MA 10",
        "ma_operator": "Cắt lên",
        "ma_right": "MA 20",
    }
    rules_ma_above = {
        "use_ma": True,
        "ma_left": "MA 10",
        "ma_operator": "Nằm trên",
        "ma_right": "MA 20",
    }
    sig_cross = evaluate_strategy_signals(df_prepared, buy_rules=rules_ma_cross)
    sig_above = evaluate_strategy_signals(df_prepared, buy_rules=rules_ma_above)
    assert np.sum(sig_above == 2) >= np.sum(sig_cross == 2)

    # 3. Tinh chỉnh Volume Spike: min 200% threshold vs min -100% threshold
    rules_vol_strict = {
        "use_volume_spike": True,
        "vol_spike_period": 10,
        "min_vol_spike_pct": 200.0,
        "max_vol_spike_pct": 1000.0,
    }
    rules_vol_loose = {
        "use_volume_spike": True,
        "vol_spike_period": 10,
        "min_vol_spike_pct": -100.0,
        "max_vol_spike_pct": 1000.0,
    }
    sig_vol_strict = evaluate_strategy_signals(df_prepared, buy_rules=rules_vol_strict)
    sig_vol_loose = evaluate_strategy_signals(df_prepared, buy_rules=rules_vol_loose)
    assert np.sum(sig_vol_loose == 2) > np.sum(sig_vol_strict == 2)


def test_fine_tuned_sell_parameters_impact():
    """Kiểm tra các thông số tinh chỉnh điều kiện bán (RSI sell min/max, logic AND/OR, MA sell) thực sự thay đổi tín hiệu Bán."""
    from vn_stock.backtest import prepare_backtest_df, evaluate_strategy_signals

    df = _create_sample_market_df(n_bars=30, start_price=30.0)
    df_prepared = prepare_backtest_df(df)

    # 1. Tinh chỉnh khoảng RSI bán: bao phủ dải cao [70, 100] vs biên thấp không đạt [10, 30]
    sell_rsi_loose = {
        "use_rsi": True,
        "rsi_min": 70.0,
        "rsi_max": 100.0,
    }
    sell_rsi_strict = {
        "use_rsi": True,
        "rsi_min": 10.0,
        "rsi_max": 30.0,
    }
    sig_loose = evaluate_strategy_signals(df_prepared, sell_rules=sell_rsi_loose)
    sig_strict = evaluate_strategy_signals(df_prepared, sell_rules=sell_rsi_strict)
    assert np.sum(sig_loose == 0) > np.sum(sig_strict == 0)

    # 2. Kiểm tra logic HOẶC (OR) vs VÀ (AND) trong điều kiện Bán
    sell_rules_or = {
        "condition_logic": "OR",
        "use_rsi": True,
        "rsi_min": 40.0,
        "rsi_max": 100.0,
        "use_adx": True,
        "min_adx": 80.0,
        "max_adx": 100.0,
    }
    sell_rules_and = {
        "condition_logic": "AND",
        "use_rsi": True,
        "rsi_min": 40.0,
        "rsi_max": 100.0,
        "use_adx": True,
        "min_adx": 80.0,
        "max_adx": 100.0,
    }
    sig_or = evaluate_strategy_signals(df_prepared, sell_rules=sell_rules_or)
    sig_and = evaluate_strategy_signals(df_prepared, sell_rules=sell_rules_and)
    assert np.sum(sig_or == 0) >= np.sum(sig_and == 0)


def test_evaluate_strategy_signals_comprehensive_indicators():
    """Kiểm tra toàn diện tất cả các nhóm điều kiện chỉ báo kỹ thuật trong evaluate_strategy_signals."""
    df = _create_sample_market_df(n_bars=30, start_price=50.0)
    df_prepared = prepare_backtest_df(df)

    # 1. Test rỗng
    sig_empty = evaluate_strategy_signals(pd.DataFrame())
    assert len(sig_empty) == 0

    # 2. Test các điều kiện Mua: MA ("Cắt lên", "Cắt xuống", "Nằm trên"), RSI, Volume Spike, P/B, Market Cap
    buy_rules_all = {
        "condition_logic": "OR",
        "use_volume_spike": True,
        "vol_spike_period": 10,
        "min_vol_spike_pct": -50.0,
        "max_vol_spike_pct": 500.0,
        "use_pb": True,
        "min_pb": 0.5,
        "max_pb": 3.0,
        "use_stock_price": True,
        "min_stock_price": 10.0,
        "max_stock_price": 200.0,
        "use_market_cap": True,
        "min_market_cap": 1000.0,
        "max_market_cap": 50000.0,
        "use_avg_trading_val": True,
        "min_avg_trading_val": 0.0,
        "max_avg_trading_val": 1000.0,
        "use_ma": True,
        "ma_left": "Giá đóng cửa",
        "ma_right": "MA 20",
        "ma_operator": "Nằm trên",
        "use_rsi": True,
        "rsi_min": 20.0,
        "rsi_max": 80.0,
        "use_price_increase": True,
        "price_t0_field": "Giá đóng cửa T0",
        "price_t1_field": "Giá đóng cửa T-1",
        "price_t0_operator": ">",
        "use_ema": True,
        "ema_left": "EMA 10",
        "ema_right": "EMA 20",
        "ema_operator": "Nằm trên",
        "use_macd": True,
        "macd_operator": "Nằm trên",
        "use_bb": True,
        "bb_operator": "Nằm trên",
    }
    signals = evaluate_strategy_signals(
        df_prepared,
        buy_rules=buy_rules_all,
        symbol_meta={"pb": 1.5, "market_cap": 20000.0},
    )
    assert len(signals) == len(df_prepared)
    # Có ít nhất 1 phiên phát tín hiệu MUA (2)
    assert np.any(signals == 2)


def test_get_strategy_presets_and_recent_signals():
    """Kiểm tra danh mục 8 chiến thuật mẫu chuẩn DNSE và bảng tín hiệu mới nhất."""
    presets = get_strategy_presets()
    assert len(presets) == 8
    for p in presets:
        assert "id" in p
        assert "name" in p
        assert "category" in p
        assert "win_rate_pct" in p
        assert "take_profit_pct" in p
        assert "stop_loss_pct" in p

    signals = get_recent_strategy_signals()
    assert isinstance(signals, list)
    assert len(signals) >= 5
    first_sig = signals[0]
    assert "symbol" in first_sig
    assert "action" in first_sig
    assert "strategy_name" in first_sig


def test_calculate_financial_metrics_edge_cases():
    """Kiểm tra hàm calculate_financial_metrics trong các tình huống biên: không có giao dịch, vốn không đổi."""
    # 1. Đường vốn hoàn toàn không đổi
    eq_flat = pd.Series([100.0] * 10)
    m_flat = calculate_financial_metrics(
        equity_series=eq_flat,
        trades=[],
        initial_capital=100.0,
    )
    assert m_flat.total_return_pct == 0.0
    assert m_flat.sharpe_ratio == 0.0
    # Khi vốn đứng yên, lợi suất thấp hơn lãi suất phi rủi ro rf_daily -> Sortino < 0 (-sqrt(252))
    assert m_flat.sortino_ratio < 0.0
    assert m_flat.max_drawdown_pct == 0.0
    assert m_flat.total_trades == 0
    assert m_flat.win_rate_pct == 0.0
    assert m_flat.profit_factor == 0.0

    # 2. Toàn bộ lệnh đều lỗ
    trades_loss = [
        TradeRecord(
            trade_id=1,
            symbol="VIC",
            order_type="SELL",
            signal_date="2026-01-01",
            exec_date="2026-01-02",
            exec_price=90.0,
            shares=100,
            gross_value=9000.0,
            fee=15.0,
            tax=10.0,
            net_cash_flow=8975.0,
            cash_after=8975.0,
            realized_pnl=-1025.0,
            realized_return_pct=-10.25,
            holding_days=3.0,
        )
    ]
    eq_down = pd.Series([100.0, 95.0, 90.0, 88.0])
    m_loss = calculate_financial_metrics(
        equity_series=eq_down,
        trades=trades_loss,
        initial_capital=100.0,
    )
    assert m_loss.total_return_pct < 0.0
    assert m_loss.winning_trades == 0
    assert m_loss.losing_trades == 1
    assert m_loss.win_rate_pct == 0.0
    assert m_loss.profit_factor == 0.0


def test_run_portfolio_backtest_sample():
    """Kiểm tra hàm run_portfolio_backtest mô phỏng danh mục đa tài sản (Equal-weight)."""
    from unittest.mock import patch

    # Mock load_local_data để trả về dữ liệu mẫu có nến OHLCV
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    prices_vic = np.linspace(40.0, 60.0, 60)
    prices_hpg = np.linspace(20.0, 30.0, 60)

    df_vic = pd.DataFrame({
        "Date": dates,
        "Symbol": ["VIC"] * 60,
        "Open": prices_vic,
        "High": prices_vic + 1.0,
        "Low": prices_vic - 1.0,
        "Close": prices_vic,
        "Volume": [1000000] * 60,
    })
    df_hpg = pd.DataFrame({
        "Date": dates,
        "Symbol": ["HPG"] * 60,
        "Open": prices_hpg,
        "High": prices_hpg + 1.0,
        "Low": prices_hpg - 1.0,
        "Close": prices_hpg,
        "Volume": [2000000] * 60,
    })

    def mock_load(symbol, **kwargs):
        return df_vic if symbol == "VIC" else df_hpg

    with patch("vn_stock.data_ingestion.load_local_data", side_effect=mock_load):
        res = run_portfolio_backtest(
            symbols=["VIC", "HPG"],
            start_date="2024-01-01",
            end_date="2024-03-31",
            initial_capital=100_000_000.0,
            model_type="none",
            buy_rules={"use_rsi": True, "rsi_min": 10.0, "rsi_max": 90.0},
            sell_rules={"take_profit_pct": 0.15, "stop_loss_pct": 0.07},
            symbol_metadata={
                "VIC": {"name": "Tập đoàn Vingroup", "sector": "Bất động sản"},
                "HPG": {"name": "Tập đoàn Hòa Phát", "sector": "Thép"},
            },
        )

        assert "aggregate_metrics" in res
        assert "portfolio_equity_curve" in res
        assert "symbols_breakdown" in res
        assert len(res["symbols_breakdown"]) == 2
        assert len(res["portfolio_equity_curve"]) > 0
        assert res["aggregate_metrics"]["initial_capital"] == 100_000_000.0


def test_backtest_symbol_oos_and_all_symbols():
    """Kiểm tra backtest_symbol_oos và backtest_all_symbols với mock test window."""
    from unittest.mock import patch
    from vn_stock.features import FEATURE_COLS

    dates = pd.date_range("2024-01-01", periods=20, freq="B")
    records = []
    for d in dates:
        row = {
            "Date": d,
            "Symbol": "VIC",
            "Open": 50.0,
            "High": 52.0,
            "Low": 48.0,
            "Close": 51.0,
            "Volume": 1000000,
            "Symbol_Code": 0,
        }
        for f in FEATURE_COLS:
            row[f] = 0.05
        records.append(row)
    mock_test_df = pd.DataFrame(records)

    mock_splits = {
        "val": mock_test_df,
        "val_warmup": mock_test_df.tail(19),
        "scaler": None,
    }

    with (
        patch("vn_stock.data_ingestion.load_panel_dataset", return_value=pd.DataFrame()),
        patch("vn_stock.features.compute_features_per_symbol", return_value=pd.DataFrame()),
        patch("vn_stock.splitting_data.apply_study_window", return_value=pd.DataFrame()),
        patch("vn_stock.splitting_data.create_multi_day_labels", return_value=pd.DataFrame()),
        patch("vn_stock.splitting_data.prepare_production_training_data", return_value=mock_splits),
    ):
        res_vic = backtest_symbol_oos(symbol="VIC", model_type="lightgbm")
        assert res_vic.symbol == "VIC"
        assert res_vic.metrics is not None
        assert res_vic.metrics.total_return_pct is not None

        df_summary = backtest_all_symbols(symbols=["VIC"], model_type="lightgbm")
        assert len(df_summary) == 1
        assert df_summary.iloc[0]["Symbol"] == "VIC"
        assert "ROI %" in df_summary.columns
        assert "Sharpe" in df_summary.columns


# ===========================================================================
# CÁC TEST CASE CHUYÊN SÂU CẤP ĐỘ UNIT (UNIT-LEVEL TEST SUITE FOR BACKTESTING)
# ===========================================================================


def test_slippage_rate_impact():
    """Kiểm tra tác động của trượt giá (Slippage): mua đắt hơn, bán rẻ hơn và giảm lợi nhuận ròng."""
    df = _create_sample_market_df(n_bars=6, start_price=100.0)
    signals = np.array([2, 1, 0, 1, 1, 1])

    # 1. Chạy không trượt giá (slippage = 0.0)
    m_no_slip, _, tr_no_slip = simulate_vietnam_trading(
        df=df,
        signals=signals,
        initial_capital=10_000_000,
        slippage_rate=0.0,
        close_at_end=False,
    )
    buy_no_slip = tr_no_slip[tr_no_slip["order_type"] == "BUY"].iloc[0]
    sell_no_slip = tr_no_slip[tr_no_slip["order_type"] == "SELL"].iloc[0]

    # 2. Chạy có trượt giá 0.5% (slippage = 0.005)
    m_with_slip, _, tr_with_slip = simulate_vietnam_trading(
        df=df,
        signals=signals,
        initial_capital=10_000_000,
        slippage_rate=0.005,
        close_at_end=False,
    )
    buy_with_slip = tr_with_slip[tr_with_slip["order_type"] == "BUY"].iloc[0]
    sell_with_slip = tr_with_slip[tr_with_slip["order_type"] == "SELL"].iloc[0]

    # Giá mua có trượt giá phải cao hơn giá cơ sở: Open * (1 + 0.005)
    assert buy_with_slip["exec_price"] > buy_no_slip["exec_price"]
    assert pytest.approx(buy_with_slip["exec_price"], 0.01) == (buy_no_slip["exec_price"] * 1.005)

    # Giá bán có trượt giá phải thấp hơn giá cơ sở: Open * (1 - 0.005)
    assert sell_with_slip["exec_price"] < sell_no_slip["exec_price"]
    assert pytest.approx(sell_with_slip["exec_price"], 0.01) == (sell_no_slip["exec_price"] * 0.995)

    # Hiệu suất tài chính khi có trượt giá phải kém hơn khi không có trượt giá
    assert m_with_slip.total_return_pct < m_no_slip.total_return_pct
    assert m_with_slip.final_equity < m_no_slip.final_equity


def test_execution_price_close_vs_open():
    """Kiểm tra cơ chế khớp lệnh tại giá Close_{t+1} thay vì Open_{t+1}."""
    dates = pd.date_range("2026-01-01", periods=5, freq="B")
    df = pd.DataFrame({
        "Date": dates,
        "Open": [100.0, 102.0, 104.0, 106.0, 108.0],
        "High": [101.0, 105.0, 107.0, 109.0, 111.0],
        "Low": [99.0, 101.0, 103.0, 105.0, 107.0],
        "Close": [101.0, 103.0, 105.0, 107.0, 109.0],
        "Volume": [1_000_000] * 5,
    })
    signals = np.array([2, 1, 1, 1, 1])

    # Khớp tại Close
    _, _, tr_close = simulate_vietnam_trading(
        df=df,
        signals=signals,
        initial_capital=10_000_000,
        slippage_rate=0.0,
        execution_price="close",
        close_at_end=False,
    )
    buy_close = tr_close[tr_close["order_type"] == "BUY"].iloc[0]
    # Ngày 1 Close = 103.0 (trong khi Open = 102.0)
    assert buy_close["exec_price"] == 103.0


def test_insufficient_cash_for_minimum_lot():
    """Kiểm tra khi tiền mặt không đủ mua tối thiểu 1 lô 100 cổ phiếu thì hệ thống từ chối lệnh."""
    # Giá 100k/cp -> 1 lô 100 cp cần 10,000k = 10,000,000 đ
    df = _create_sample_market_df(n_bars=5, start_price=100.0)
    signals = np.array([2, 1, 1, 1, 1])

    # Vốn ban đầu chỉ có 5,000 đ (nhỏ hơn nhiều so với 10 triệu đ cần thiết)
    metrics, _, trades_df = simulate_vietnam_trading(
        df=df,
        signals=signals,
        initial_capital=5_000.0,
        lot_size=100,
        close_at_end=False,
    )

    # Không có lệnh giao dịch nào được thực thi
    assert len(trades_df) == 0
    assert metrics.total_trades == 0
    assert metrics.final_equity == 5_000.0


def test_partial_settlement_unsettled_lots_retained():
    """Kiểm tra nguyên tắc bảo toàn lô chưa về: chỉ bán lô đã về T+2 và giữ lại lô chưa về."""
    # Kiểm tra trực tiếp cấu trúc PositionLot và logic phân loại tại thời điểm khớp lệnh
    lot_settled = PositionLot(
        shares=100,
        buy_price=50.0,
        cost_basis=5007.5,
        buy_idx=1,
        buy_date="2026-01-02",
        settled_idx=3,
        highest_price=50.0,
    )
    lot_unsettled = PositionLot(
        shares=200,
        buy_price=52.0,
        cost_basis=10415.6,
        buy_idx=2,
        buy_date="2026-01-05",
        settled_idx=4,
        highest_price=52.0,
    )
    inventory = [lot_settled, lot_unsettled]

    # Tại exec_idx = 3 (ngày Lô 1 về, Lô 2 chưa về)
    exec_idx = 3
    settled_lots = [lot for lot in inventory if lot.settled_idx <= exec_idx]
    unsettled_lots = [lot for lot in inventory if lot.settled_idx > exec_idx]

    assert len(settled_lots) == 1
    assert settled_lots[0].shares == 100
    assert len(unsettled_lots) == 1
    assert unsettled_lots[0].shares == 200

    # Sau khi bán lô settled, inventory chỉ còn lô unsettled
    inventory = unsettled_lots
    assert len(inventory) == 1
    assert inventory[0].shares == 200
    assert inventory[0].settled_idx == 4


def test_take_profit_mechanism_execution():
    """Kiểm tra cơ chế Chốt lời (Take Profit): kích hoạt bán khi giá tăng >= take_profit_pct sau T+2."""
    dates = pd.date_range("2026-01-01", periods=6, freq="B")
    df = pd.DataFrame({
        "Date": dates,
        "Open": [100.0, 100.0, 105.0, 118.0, 120.0, 122.0],
        "High": [101.0, 101.0, 106.0, 119.0, 121.0, 123.0],
        "Low": [99.0, 99.0, 104.0, 117.0, 119.0, 121.0],
        "Close": [100.0, 100.0, 105.0, 118.0, 120.0, 122.0],
        "Volume": [1_000_000] * 6,
    })
    signals = np.array([2, 1, 1, 1, 1, 1])

    res = run_backtest(
        df=df,
        signals=signals,
        symbol="FPT",
        initial_capital=50_000_000,
        take_profit_pct=0.15,  # Chốt lời 15%
        close_at_end=False,
    )

    sell_trades = res.trades_df[res.trades_df["order_type"] == "SELL"]
    assert len(sell_trades) == 1
    assert sell_trades.iloc[0]["reason"] == "TAKE_PROFIT"
    assert sell_trades.iloc[0]["exec_price"] >= 115.0
    assert sell_trades.iloc[0]["realized_pnl"] > 0


def test_trailing_stop_mechanism_execution():
    """Kiểm tra cơ chế Trailing Stop: theo dõi đỉnh cao nhất và bán khi giá sụt giảm >= trailing_stop_pct."""
    dates = pd.date_range("2026-01-01", periods=7, freq="B")
    df = pd.DataFrame({
        "Date": dates,
        "Open": [100.0, 100.0, 110.0, 125.0, 114.0, 110.0, 108.0],
        "High": [101.0, 101.0, 111.0, 126.0, 115.0, 111.0, 109.0],
        "Low": [99.0, 99.0, 109.0, 124.0, 113.0, 109.0, 107.0],
        "Close": [100.0, 100.0, 110.0, 125.0, 114.0, 110.0, 108.0],
        "Volume": [1_000_000] * 7,
    })
    signals = np.array([2, 1, 1, 1, 1, 1, 1])

    res = run_backtest(
        df=df,
        signals=signals,
        symbol="VIC",
        initial_capital=50_000_000,
        trailing_stop_pct=0.08,  # Trailing Stop 8%
        close_at_end=False,
    )

    sell_trades = res.trades_df[res.trades_df["order_type"] == "SELL"]
    assert len(sell_trades) == 1
    assert sell_trades.iloc[0]["reason"] == "TRAILING_STOP"
    assert sell_trades.iloc[0]["exec_date"] == df.iloc[4]["Date"].strftime("%Y-%m-%d")


def test_close_at_end_true_vs_false():
    """Kiểm tra tham số close_at_end: thanh lý cưỡng bức ở phiên cuối vs giữ nguyên vị thế mở."""
    df = _create_sample_market_df(n_bars=6, start_price=50.0)
    signals = np.array([2, 1, 1, 1, 1, 1])

    # 1. close_at_end = True -> Phải có lệnh bán FINAL_LIQUIDATION ở phiên cuối
    _, _, tr_true = simulate_vietnam_trading(
        df=df,
        signals=signals,
        initial_capital=20_000_000,
        close_at_end=True,
    )
    assert len(tr_true[tr_true["order_type"] == "SELL"]) == 1
    assert tr_true.iloc[-1]["reason"] == "FINAL_LIQUIDATION"

    # 2. close_at_end = False -> Không có lệnh bán nào được sinh ra vì AI không phát tín hiệu SELL
    _, _, tr_false = simulate_vietnam_trading(
        df=df,
        signals=signals,
        initial_capital=20_000_000,
        close_at_end=False,
    )
    assert len(tr_false[tr_false["order_type"] == "SELL"]) == 0


def test_custom_settlement_delays():
    """Kiểm tra linh hoạt các chu kỳ thanh toán khác nhau: T+0, T+1 và T+2."""
    df = _create_sample_market_df(n_bars=5, start_price=50.0)
    signals = np.array([2, 0, 1, 1, 1])

    # Với T+0 (settlement_delay = 0): Mua ngày 1, bán được ngay tại ngày 1 hoặc ngày 2
    _, _, tr_t0 = simulate_vietnam_trading(
        df=df,
        signals=signals,
        initial_capital=20_000_000,
        settlement_delay=0,
        close_at_end=False,
    )
    sell_t0 = tr_t0[tr_t0["order_type"] == "SELL"]
    assert len(sell_t0) == 1
    assert sell_t0.iloc[0]["exec_date"] == df.iloc[2]["Date"].strftime("%Y-%m-%d")

    # Với T+2 (settlement_delay = 2): Mua ngày 1, ngày 2 đòi bán -> BỊ TỪ CHỐI, không khớp!
    _, _, tr_t2 = simulate_vietnam_trading(
        df=df,
        signals=signals,
        initial_capital=20_000_000,
        settlement_delay=2,
        close_at_end=False,
    )
    sell_t2 = tr_t2[tr_t2["order_type"] == "SELL"]
    assert len(sell_t2) == 0


def test_calculate_financial_metrics_cagr_and_calmar():
    """Kiểm tra công thức CAGR cho các khoảng thời gian khác nhau và tỷ số Calmar."""
    # 252 ngày giao dịch (1 năm): Vốn tăng từ 100 lên 120 -> CAGR = 20%
    eq_1y = pd.Series(np.linspace(100.0, 120.0, 252))
    m_1y = calculate_financial_metrics(eq_1y, initial_capital=100.0, trades=[])
    assert pytest.approx(m_1y.cagr_pct, 0.1) == 20.0
    assert m_1y.total_return_pct == 20.0

    # 504 ngày giao dịch (2 năm): Vốn tăng từ 100 lên 144 -> CAGR = sqrt(1.44) - 1 = 20%
    eq_2y = pd.Series(np.linspace(100.0, 144.0, 504))
    m_2y = calculate_financial_metrics(eq_2y, initial_capital=100.0, trades=[])
    assert pytest.approx(m_2y.cagr_pct, 0.1) == 20.0

    # Khi tài khoản bị cháy (final_equity <= 0)
    eq_ruin = pd.Series([100.0, 50.0, 0.0])
    m_ruin = calculate_financial_metrics(eq_ruin, initial_capital=100.0, trades=[])
    assert m_ruin.cagr_pct == -100.0


def test_calculate_financial_metrics_var_and_cvar():
    """Kiểm tra giá trị chịu rủi ro VaR 95% và CVaR 95% (Expected Shortfall)."""
    np.random.seed(42)
    daily_rets = np.random.normal(0.001, 0.02, 100)
    eq_series = pd.Series(100.0 * np.cumprod(1 + daily_rets))

    metrics = calculate_financial_metrics(eq_series, initial_capital=100.0, trades=[])
    assert metrics.var_95_pct > 0.0
    assert metrics.cvar_95_pct >= metrics.var_95_pct


def test_calculate_financial_metrics_profit_factor_pure_win():
    """Kiểm tra khi toàn bộ lệnh đều có lãi (gross_loss = 0) thì profit_factor = 999.0."""
    trade_win = TradeRecord(
        trade_id=1,
        symbol="VIC",
        order_type="SELL",
        signal_date="2026-01-01",
        exec_date="2026-01-03",
        exec_price=110.0,
        shares=100,
        gross_value=11000.0,
        fee=15.0,
        tax=10.0,
        net_cash_flow=10975.0,
        cash_after=10975.0,
        realized_pnl=975.0,
        realized_return_pct=9.75,
        holding_days=2.0,
    )
    eq = pd.Series([100.0, 105.0, 110.0])
    metrics = calculate_financial_metrics(eq, initial_capital=100.0, trades=[trade_win])

    assert metrics.winning_trades == 1
    assert metrics.losing_trades == 0
    assert metrics.win_rate_pct == 100.0
    assert metrics.profit_factor == 999.0


def test_run_random_baseline_deterministic_seed():
    """Kiểm tra tính nhất quán của hàm run_random_baseline khi cố định seed."""
    df = _create_sample_market_df(n_bars=10, start_price=50.0)

    res1 = run_random_baseline(df, symbol="VIC", initial_capital=20_000_000, seed=123)
    res2 = run_random_baseline(df, symbol="VIC", initial_capital=20_000_000, seed=123)

    assert res1.metrics.total_return_pct == res2.metrics.total_return_pct
    assert res1.metrics.final_equity == res2.metrics.final_equity
    assert res1.metrics.equity_curve == res2.metrics.equity_curve


def test_prepare_backtest_df_all_technical_features():
    """Kiểm tra prepare_backtest_df tính toán đầy đủ tất cả các chỉ báo kỹ thuật tài chính."""
    df = _create_sample_market_df(n_bars=40, start_price=50.0)
    df_prep = prepare_backtest_df(df)

    expected_cols = [
        "SMA5", "SMA10", "SMA20", "SMA50", "SMA100", "SMA200",
        "EMA5", "EMA10", "EMA12", "EMA20", "EMA26", "EMA50",
        "RSI", "MACD", "MACD_Signal",
        "BB_Upper", "BB_Lower",
        "Vol_SMA5", "Vol_SMA10", "Vol_SMA20",
        "ADX", "RS",
    ]
    for col in expected_cols:
        assert col in df_prep.columns


def test_evaluate_strategy_signals_ma_down_cross_and_below():
    """Kiểm tra toán tử 'Cắt xuống' và 'Nằm dưới' trong evaluate_strategy_signals."""
    dates = pd.date_range("2026-01-01", periods=20, freq="B")
    # Giá giảm dần từ 100 về 80
    prices = [100.0 - i * 1.0 for i in range(20)]
    df = pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": [p + 0.5 for p in prices],
        "Low": [p - 0.5 for p in prices],
        "Close": prices,
        "Volume": [1_000_000] * 20,
    })
    df_prep = prepare_backtest_df(df)

    # Bán khi MA10 nằm dưới MA20
    sell_rules_below = {
        "use_ma": True,
        "ma_left": "MA 10",
        "ma_operator": "Nằm dưới",
        "ma_right": "MA 20",
    }
    signals_below = evaluate_strategy_signals(df_prep, sell_rules=sell_rules_below)
    assert any(s == 0 for s in signals_below)

    # Bán khi MA10 cắt xuống MA20
    sell_rules_cross = {
        "use_ma": True,
        "ma_left": "MA 10",
        "ma_operator": "Cắt xuống",
        "ma_right": "MA 20",
    }
    signals_cross = evaluate_strategy_signals(df_prep, sell_rules=sell_rules_cross)
    assert len(signals_cross) == len(df_prep)


def test_evaluate_strategy_signals_foreign_and_prop_rules():
    """Kiểm tra bộ lọc giao dịch khối ngoại (nước ngoài) và tự doanh trong evaluate_strategy_signals."""
    df = _create_sample_market_df(n_bars=10, start_price=50.0)
    df_prep = prepare_backtest_df(df)

    # Thêm dữ liệu khối ngoại và tự doanh
    df_prep["Foreign_Buy_Val"] = [10.0] * 10
    df_prep["Foreign_Sell_Val"] = [5.0] * 10  # Mua ròng 5 tỷ
    df_prep["Foreign_Buy_Vol"] = [2.0] * 10
    df_prep["Foreign_Sell_Vol"] = [1.0] * 10  # Mua ròng 1 tr cp
    df_prep["Prop_Buy_Val"] = [8.0] * 10
    df_prep["Prop_Sell_Val"] = [3.0] * 10  # Tự doanh mua ròng 5 tỷ
    df_prep["Prop_Buy_Vol"] = [1.5] * 10
    df_prep["Prop_Sell_Vol"] = [0.5] * 10

    buy_rules_foreign = {
        "condition_logic": "AND",
        "foreign_net_buy": True,
        "foreign_net_buy_val": True,
        "min_foreign_buy_val": 2.0,
        "foreign_net_buy_vol": True,
        "min_foreign_buy_vol": 0.5,
        "prop_net_buy_val": True,
        "min_prop_buy_val": 2.0,
        "prop_net_buy_vol": True,
        "min_prop_buy_vol": 0.5,
    }

    signals = evaluate_strategy_signals(df_prep, buy_rules=buy_rules_foreign)
    # Tất cả các phiên đều thỏa mãn điều kiện mua ròng khối ngoại & tự doanh
    assert all(s == 2 for s in signals)


def test_position_lot_and_trade_record_dataclass_contracts():
    """Kiểm tra hợp đồng dữ liệu của PositionLot, TradeRecord và to_dict()."""
    lot = PositionLot(
        shares=500,
        buy_price=50.0,
        cost_basis=25037.5,
        buy_idx=1,
        buy_date="2026-01-02",
        settled_idx=3,
        highest_price=52.0,
    )
    assert lot.shares == 500
    assert lot.settled_idx == 3
    assert lot.highest_price == 52.0

    tr = TradeRecord(
        trade_id=1,
        symbol="VIC",
        order_type="BUY",
        signal_date="2026-01-01",
        exec_date="2026-01-02",
        exec_price=50.0,
        shares=500,
        gross_value=25000.0,
        fee=37.5,
        tax=0.0,
        net_cash_flow=-25037.5,
        cash_after=74962.5,
        reason="SIGNAL_BUY",
    )
    assert tr.net_cash_flow == -25037.5
    assert tr.fee == 37.5
    assert tr.tax == 0.0







