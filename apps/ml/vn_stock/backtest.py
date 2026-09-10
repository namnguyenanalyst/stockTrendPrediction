"""Module mô phỏng kiểm thử chiến lược đầu tư (Backtesting Engine) có tính chi phí giao dịch thực tế tại Việt Nam."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import numpy as np
import pandas as pd

from vn_stock.config import INITIAL_CAPITAL, LOT_SIZE, TAX_RATE, TRANSACTION_FEE_RATE


@dataclass
class BacktestMetrics:
    initial_capital: float
    final_equity: float
    total_return_pct: float
    buy_and_hold_return_pct: float
    win_rate_pct: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    equity_curve: List[float] = field(default_factory=list)


def run_simple_backtest(
    prices: np.ndarray,
    predictions: np.ndarray,
    initial_capital: float = INITIAL_CAPITAL,
    fee_rate: float = TRANSACTION_FEE_RATE,
    tax_rate: float = TAX_RATE,
    buy_threshold: float = 0.015,   # Dự báo tăng > 1.5% thì MUA
    sell_threshold: float = -0.015, # Dự báo giảm < -1.5% thì BÁN
) -> BacktestMetrics:
    """
    Chạy mô phỏng giao dịch theo tín hiệu dự báo của mô hình AI:
    - Trừ phí mua (0.15%)
    - Trừ phí bán (0.15%) + thuế bán (0.10%)
    - Khớp lệnh theo lô và bảo toàn số dư tiền mặt
    """
    cash = float(initial_capital)
    shares = 0
    trade_count = 0
    winning_trades = 0
    losing_trades = 0
    last_buy_price = 0.0
    equity_curve: List[float] = []

    for i in range(len(prices) - 1):
        curr_price = float(prices[i])
        next_pred = float(predictions[i])
        expected_return = (next_pred - curr_price) / curr_price if curr_price > 0 else 0

        # Tín hiệu MUA
        if expected_return > buy_threshold and cash > curr_price * LOT_SIZE:
            # Mua số lượng cổ phiếu tối đa theo lô chẵn
            available_shares = int(cash // (curr_price * (1 + fee_rate)))
            lot_shares = (available_shares // LOT_SIZE) * LOT_SIZE
            if lot_shares > 0:
                cost = lot_shares * curr_price * (1 + fee_rate)
                cash -= cost
                shares += lot_shares
                last_buy_price = curr_price
                trade_count += 1

        # Tín hiệu BÁN
        elif expected_return < sell_threshold and shares > 0:
            gross_proceeds = shares * curr_price
            # Phí bán + thuế bán
            net_proceeds = gross_proceeds * (1 - fee_rate - tax_rate)
            cash += net_proceeds
            if curr_price > last_buy_price:
                winning_trades += 1
            else:
                losing_trades += 1
            shares = 0
            trade_count += 1

        total_value = cash + (shares * curr_price)
        equity_curve.append(total_value)

    # Đóng vị thế vào ngày cuối cùng
    final_price = float(prices[-1])
    if shares > 0:
        cash += shares * final_price * (1 - fee_rate - tax_rate)
        shares = 0
    final_equity = cash
    equity_curve.append(final_equity)

    # Tính toán các chỉ số
    total_return_pct = ((final_equity - initial_capital) / initial_capital) * 100
    buy_and_hold_return_pct = (
        ((prices[-1] - prices[0]) / prices[0]) * 100 if prices[0] > 0 else 0.0
    )
    closed_trades = winning_trades + losing_trades
    win_rate_pct = (winning_trades / closed_trades * 100) if closed_trades > 0 else 0.0

    # Max Drawdown
    equity_arr = np.array(equity_curve)
    peak = np.maximum.accumulate(equity_arr)
    drawdowns = (equity_arr - peak) / peak
    max_drawdown_pct = float(np.min(drawdowns) * 100) if len(drawdowns) > 0 else 0.0

    return BacktestMetrics(
        initial_capital=initial_capital,
        final_equity=round(final_equity, 2),
        total_return_pct=round(total_return_pct, 2),
        buy_and_hold_return_pct=round(buy_and_hold_return_pct, 2),
        win_rate_pct=round(win_rate_pct, 2),
        max_drawdown_pct=round(abs(max_drawdown_pct), 2),
        total_trades=trade_count,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        equity_curve=[round(x, 2) for x in equity_curve],
    )
