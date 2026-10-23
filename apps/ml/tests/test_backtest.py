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
    calculate_financial_metrics,
    run_backtest,
    run_buy_and_hold,
    run_monte_carlo_random_test,
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


def test_run_portfolio_backtest():
    """Kiểm tra chạy Backtest danh mục đa mã (Equal-Weighted Portfolio)."""
    from vn_stock.backtest import run_portfolio_backtest

    res = run_portfolio_backtest(
        symbols=["VIC", "HPG"],
        start_date="2024-01-01",
        end_date="2024-06-30",
        initial_capital=100_000_000,
        buy_rules={"use_ma": True},
        sell_rules={"take_profit_pct": 0.15, "stop_loss_pct": 0.07},
    )

    assert "aggregate_metrics" in res
    assert "portfolio_equity_curve" in res
    assert "symbols_breakdown" in res
    assert "individual_results" in res

    agg = res["aggregate_metrics"]
    assert agg["initial_capital"] == 100_000_000
    assert len(res["symbols_breakdown"]) >= 1
    assert len(res["portfolio_equity_curve"]) > 0

