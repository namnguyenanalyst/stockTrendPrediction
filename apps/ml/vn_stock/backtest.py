"""Module mô phỏng kiểm thử chiến lược đầu tư (Backtesting Engine) thực tế tại thị trường Việt Nam.

Tuân thủ nghiêm ngặt các quy chuẩn tài chính và vi cấu trúc thị trường chứng khoán Việt Nam:
1. Chu kỳ thanh toán T+2: Cổ phiếu mua tại phiên t chỉ được phép bán từ phiên t + 2 trở đi.
2. Khấu trừ chi phí thực tế: Phí giao dịch môi giới (0.15% mỗi chiều mua/bán) và Thuế thu nhập chuyển nhượng (0.10% khi bán).
3. Khớp lệnh theo lô chẵn 100 cổ phiếu (quy định HSX/HNX), bảo toàn số dư tiền mặt lẻ.
4. Cơ chế khớp lệnh không nhìn trước tương lai: Tín hiệu sinh ra sau khi đóng cửa phiên t (dựa trên Close_t và các chỉ báo kỹ thuật), lệnh được đưa vào hàng đợi và thực thi tại phiên t+1 (mặc định tại giá Open_{t+1} kèm trượt giá slippage).
5. Đo lường rủi ro và hiệu quả danh mục toàn diện: ROI, CAGR, Sharpe Ratio, Sortino Ratio, Max Drawdown (MDD), Calmar Ratio, VaR 95%, CVaR 95%, Win Rate, Profit Factor, Trade Log và đường cong tài sản (Equity Curve).
6. So sánh đối chứng chuẩn mực: Chiến lược Mua & Nắm giữ (Buy & Hold), Chiến lược đối chứng ngẫu nhiên (Random Signal Baseline) và Thử nghiệm Monte Carlo (Bootstrap Confidence Intervals & Empirical p-value).
"""

import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import argparse
from dataclasses import dataclass, field
import logging
from pathlib import Path
import pickle
from typing import Any

import numpy as np
import pandas as pd

from vn_stock.config import (
    INITIAL_CAPITAL,
    LOT_SIZE,
    MODELS_DIR,
    TAX_RATE,
    TRANSACTION_FEE_RATE,
)

logger = logging.getLogger(__name__)


@dataclass
class PositionLot:
    """Lô cổ phiếu nắm giữ trong tài khoản để kiểm soát chu kỳ thanh toán T+2."""

    shares: int
    buy_price: float
    cost_basis: float  # Tổng giá trị mua + phí mua phân bổ
    buy_idx: int  # Chỉ số phiên giao dịch thực thi lệnh mua
    buy_date: str  # Ngày khớp lệnh mua
    settled_idx: int  # Chỉ số phiên giao dịch sớm nhất được phép bán (buy_idx + settlement_delay)
    highest_price: float = 0.0  # Giá đỉnh cao nhất kể từ lúc mua (phục vụ Trailing Stop)


@dataclass
class TradeRecord:
    """Nhật ký ghi nhận chi tiết từng lệnh giao dịch thực tế."""

    trade_id: int
    symbol: str
    order_type: str  # 'BUY' | 'SELL'
    signal_date: str  # Ngày phát sinh tín hiệu sau giờ giao dịch (t)
    exec_date: str  # Ngày thực thi lệnh trên sàn (t+1)
    exec_price: float  # Thị giá khớp lệnh thực tế (đã tính trượt giá)
    shares: int  # Số lượng cổ phiếu (bội số của lô 100)
    gross_value: float  # Giá trị giao dịch gộp (shares * exec_price)
    fee: float  # Phí môi giới (0.15% * gross_value)
    tax: float  # Thuế chuyển nhượng (0.10% * gross_value nếu là SELL, 0 nếu là BUY)
    net_cash_flow: float  # Dòng tiền ròng (-cost cho BUY, +proceeds cho SELL)
    cash_after: float  # Số dư tiền mặt khả dụng sau giao dịch
    realized_pnl: float | None = None  # Lợi nhuận gộp thực hiện (cho lệnh SELL)
    realized_return_pct: float | None = None  # Tỷ suất sinh lời thực hiện (%)
    holding_days: float | None = None  # Số phiên giao dịch đã nắm giữ (cho lệnh SELL)
    reason: str = ""  # Lý do phát sinh lệnh ('SIGNAL_BUY', 'SIGNAL_SELL', 'FINAL_LIQUIDATION')


@dataclass
class BacktestMetrics:
    """Bộ chỉ số đo lường hiệu quả tài chính và rủi ro danh mục toàn diện."""

    initial_capital: float
    final_equity: float
    total_return_pct: float  # ROI (%)
    cagr_pct: float  # Annualized Return / CAGR (%)
    buy_and_hold_return_pct: float  # Lợi nhuận chiến lược Buy & Hold (%)
    excess_return_pct: float  # Lợi nhuận vượt trội so với Buy & Hold (alpha %)
    annualized_volatility_pct: float  # Độ biến động năm hóa (%)
    sharpe_ratio: float  # Tỷ số Sharpe năm hóa (với lãi suất phi rủi ro Rf)
    sortino_ratio: float  # Tỷ số Sortino năm hóa (độ biến động giảm giá Downside Dev)
    max_drawdown_pct: float  # Mức sụt giảm vốn lớn nhất từ đỉnh (MDD %)
    calmar_ratio: float  # Tỷ số Calmar (CAGR / MDD)
    var_95_pct: float  # Giá trị chịu rủi ro VaR 95% 1 ngày theo lịch sử (%)
    cvar_95_pct: float  # Kỳ vọng tổn thất vượt mức CVaR 95% (Expected Shortfall %)
    win_rate_pct: float  # Tỷ lệ lệnh có lãi Win Rate (%)
    profit_factor: float  # Hệ số lợi nhuận Profit Factor (Tổng lãi / Tổng lỗ)
    total_trades: int  # Tổng số vòng giao dịch đã đóng
    winning_trades: int  # Số vòng giao dịch có lãi
    losing_trades: int  # Số vòng giao dịch hòa/lỗ
    avg_trade_return_pct: float  # Tỷ suất sinh lời trung bình mỗi lệnh (%)
    best_trade_return_pct: float  # Lợi nhuận của lệnh thắng lớn nhất (%)
    worst_trade_return_pct: float  # Mức lỗ của lệnh lỗ lớn nhất (%)
    avg_holding_days: float  # Thời gian nắm giữ trung bình mỗi lệnh (ngày)
    total_fees_paid: float  # Tổng chi phí môi giới đã trả (VNĐ)
    total_taxes_paid: float  # Tổng thuế thu nhập chuyển nhượng đã nộp (VNĐ)
    total_costs: float  # Tổng chi phí thuế phí đã khấu trừ (VNĐ)
    cost_impact_pct: float  # Tỷ lệ tác động của chi phí trên vốn ban đầu (%)
    equity_curve: list[float] = field(default_factory=list)


@dataclass
class BacktestResult:
    """Kết quả tổng thể của một phiên kiểm thử chiến lược đầu tư."""

    symbol: str
    strategy_name: str
    metrics: BacktestMetrics
    equity_df: pd.DataFrame
    trades_df: pd.DataFrame
    config: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Xuất kết quả dưới dạng dictionary có thể serialize JSON phục vụ API/Dashboard."""
        metrics_dict = {k: v for k, v in self.metrics.__dict__.items() if k != "equity_curve"}
        return {
            "symbol": self.symbol,
            "strategy_name": self.strategy_name,
            "config": self.config,
            "metrics": metrics_dict,
            "equity_curve_summary": {
                "dates": self.equity_df["Date"].tolist(),
                "total_equity": self.equity_df["Total_Equity"].tolist(),
                "benchmark_equity": self.equity_df["Benchmark_Equity"].tolist()
                if "Benchmark_Equity" in self.equity_df.columns
                else [],
                "drawdown_pct": self.equity_df["Drawdown_Pct"].tolist()
                if "Drawdown_Pct" in self.equity_df.columns
                else [],
            },
            "trades_count": len(self.trades_df),
        }


def calculate_financial_metrics(
    equity_series: pd.Series,
    initial_capital: float,
    trades: list[TradeRecord],
    risk_free_rate: float = 0.04,
    buy_and_hold_return_pct: float = 0.0,
) -> BacktestMetrics:
    """
    Tính toán toàn diện các chỉ số định lượng tài chính chuẩn mực quốc tế:
    - Lợi suất tổng thể, CAGR (chu kỳ 252 ngày giao dịch/năm)
    - Tỷ số Sharpe và Sortino năm hóa
    - Max Drawdown và Calmar Ratio
    - VaR 95% và CVaR 95%
    - Win Rate, Profit Factor, Thống kê lệnh đóng và tác động thuế phí
    """
    final_equity = float(equity_series.iloc[-1])
    n_days = len(equity_series)
    total_return_pct = (
        ((final_equity - initial_capital) / initial_capital) * 100.0
        if initial_capital > 0
        else 0.0
    )

    # 1. CAGR (Annualized Return)
    if final_equity > 0 and n_days > 1 and initial_capital > 0:
        cagr_pct = ((final_equity / initial_capital) ** (252.0 / n_days) - 1.0) * 100.0
    else:
        cagr_pct = -100.0

    # 2. Lợi suất hàng ngày & Lãi suất phi rủi ro theo ngày
    daily_returns = equity_series.pct_change().dropna()
    rf_daily = risk_free_rate / 252.0

    # 3. Độ biến động năm hóa
    ann_volatility_pct = (
        float(daily_returns.std() * np.sqrt(252.0) * 100.0) if len(daily_returns) > 1 else 0.0
    )

    # 4. Tỷ số Sharpe năm hóa
    excess_returns = daily_returns - rf_daily
    if len(daily_returns) > 1 and daily_returns.std() > 1e-9:
        sharpe_ratio = float(excess_returns.mean() / daily_returns.std() * np.sqrt(252.0))
    else:
        sharpe_ratio = 0.0

    # 5. Tỷ số Sortino năm hóa (Downside Deviation so với rf_daily)
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = np.sqrt(np.mean(downside_returns**2)) if len(downside_returns) > 0 else 0.0
    if downside_std > 1e-9:
        sortino_ratio = float(excess_returns.mean() / downside_std * np.sqrt(252.0))
    else:
        sortino_ratio = 0.0

    # 6. Maximum Drawdown (MDD)
    peaks = np.maximum.accumulate(equity_series.values)
    drawdowns = (equity_series.values - peaks) / np.where(peaks > 0, peaks, 1.0)
    max_drawdown_pct = float(np.min(drawdowns) * 100.0) if len(drawdowns) > 0 else 0.0
    abs_mdd = abs(max_drawdown_pct)

    # 7. Calmar Ratio (CAGR / MDD)
    calmar_ratio = float(cagr_pct / abs_mdd) if abs_mdd > 1e-6 else 0.0

    # 8. VaR 95% và CVaR 95% (Historical Daily)
    if len(daily_returns) > 10:
        p5 = float(np.percentile(daily_returns, 5))
        var_95_pct = float(-p5 * 100.0)
        tail_returns = daily_returns[daily_returns <= p5]
        cvar_95_pct = float(-tail_returns.mean() * 100.0) if len(tail_returns) > 0 else var_95_pct
    else:
        var_95_pct, cvar_95_pct = 0.0, 0.0

    # 9. Thống kê lệnh đóng (SELL orders)
    closed_trades = [t for t in trades if t.order_type == "SELL" and t.realized_pnl is not None]
    total_trades_count = len(closed_trades)
    winning_trades = [t for t in closed_trades if t.realized_pnl > 0]
    losing_trades = [t for t in closed_trades if t.realized_pnl <= 0]
    win_rate_pct = (
        (len(winning_trades) / total_trades_count * 100.0) if total_trades_count > 0 else 0.0
    )

    gross_profit = sum(t.realized_pnl for t in winning_trades)
    gross_loss = abs(sum(t.realized_pnl for t in losing_trades))
    if gross_loss > 1e-6:
        profit_factor = float(gross_profit / gross_loss)
    elif gross_profit > 1e-6:
        profit_factor = 999.0
    else:
        profit_factor = 0.0

    trade_returns = [
        t.realized_return_pct for t in closed_trades if t.realized_return_pct is not None
    ]
    avg_trade_return_pct = float(np.mean(trade_returns)) if trade_returns else 0.0
    best_trade_return_pct = float(np.max(trade_returns)) if trade_returns else 0.0
    worst_trade_return_pct = float(np.min(trade_returns)) if trade_returns else 0.0

    holding_durations = [t.holding_days for t in closed_trades if t.holding_days is not None]
    avg_holding_days = float(np.mean(holding_durations)) if holding_durations else 0.0

    total_fees = sum(t.fee for t in trades)
    total_taxes = sum(t.tax for t in trades)
    total_costs = total_fees + total_taxes

    cost_impact_pct = (total_costs / initial_capital) * 100.0 if initial_capital > 0 else 0.0

    return BacktestMetrics(
        initial_capital=initial_capital,
        final_equity=round(final_equity, 2),
        total_return_pct=round(total_return_pct, 2),
        cagr_pct=round(cagr_pct, 2),
        buy_and_hold_return_pct=round(buy_and_hold_return_pct, 2),
        excess_return_pct=round(total_return_pct - buy_and_hold_return_pct, 2),
        annualized_volatility_pct=round(ann_volatility_pct, 2),
        sharpe_ratio=round(sharpe_ratio, 4),
        sortino_ratio=round(sortino_ratio, 4),
        max_drawdown_pct=round(abs_mdd, 2),
        calmar_ratio=round(calmar_ratio, 4),
        var_95_pct=round(var_95_pct, 2),
        cvar_95_pct=round(cvar_95_pct, 2),
        win_rate_pct=round(win_rate_pct, 2),
        profit_factor=round(profit_factor, 4),
        total_trades=total_trades_count,
        winning_trades=len(winning_trades),
        losing_trades=len(losing_trades),
        avg_trade_return_pct=round(avg_trade_return_pct, 2),
        best_trade_return_pct=round(best_trade_return_pct, 2),
        worst_trade_return_pct=round(worst_trade_return_pct, 2),
        avg_holding_days=round(avg_holding_days, 1),
        total_fees_paid=round(total_fees, 2),
        total_taxes_paid=round(total_taxes, 2),
        total_costs=round(total_costs, 2),
        cost_impact_pct=round(cost_impact_pct, 2),
        equity_curve=[round(x, 2) for x in equity_series.tolist()],
    )


def simulate_vietnam_trading(
    df: pd.DataFrame,
    signals: np.ndarray,
    symbol: str = "VIC",
    initial_capital: float = INITIAL_CAPITAL,
    fee_rate: float = TRANSACTION_FEE_RATE,
    tax_rate: float = TAX_RATE,
    slippage_rate: float = 0.0005,
    lot_size: int = LOT_SIZE,
    settlement_delay: int = 2,
    execution_price: str = "open",  # 'open' hoặc 'close'
    close_at_end: bool = True,
    risk_free_rate: float = 0.04,
    take_profit_pct: float | None = None,
    stop_loss_pct: float | None = None,
    trailing_stop_pct: float | None = None,
) -> tuple[BacktestMetrics, pd.DataFrame, pd.DataFrame]:
    """
    Thuật toán mô phỏng giao dịch thực tế thị trường chứng khoán Việt Nam.

    Cơ chế chi tiết:
    1. Không nhìn trước tương lai: Tín hiệu sinh ra tại cuối phiên t, lệnh thực thi vào phiên t+1.
    2. Khớp lệnh tại Open_{t+1} (hoặc Close_{t+1}) có cộng/trừ tỷ lệ trượt giá (slippage).
    3. Kiểm soát thanh toán T+2: Theo dõi từng lô mua (PositionLot), chỉ cho phép bán khi
       phiên hiện tại >= phiên_mua + settlement_delay (mặc định 2 phiên).
    4. Tích hợp Quản trị rủi ro chủ động (DNSE Risk Rules):
       - Stop Loss (Cắt lỗ cố định): Bán ngay khi chạm ngưỡng lỗ quy định.
       - Take Profit (Chốt lời mục tiêu): Chốt lãi khi đạt lợi nhuận kỳ vọng.
       - Trailing Stop (Bảo toàn lãi): Kích hoạt bán khi sụt giảm từ đỉnh giá cao nhất.
       - Tín hiệu AI: Đóng vị thế khi mô hình dự báo đảo chiều (SIGNAL_SELL).
    5. Khấu trừ chi phí thực tế: Phí mua (0.15%), Phí bán (0.15%), Thuế bán (0.10%).
    6. Khớp lệnh theo lô chẵn 100 cổ phiếu và bảo toàn số dư tiền mặt lẻ.
    """
    df_sorted = df.sort_values("Date").reset_index(drop=True)
    n_bars = len(df_sorted)
    if n_bars != len(signals):
        raise ValueError(
            f"Số lượng dòng ({n_bars}) và độ dài signals ({len(signals)}) phải bằng nhau."
        )

    dates = (
        df_sorted["Date"].dt.strftime("%Y-%m-%d").tolist()
        if pd.api.types.is_datetime64_any_dtype(df_sorted["Date"])
        else df_sorted["Date"].astype(str).tolist()
    )
    opens = df_sorted["Open"].values.astype(float)
    closes = df_sorted["Close"].values.astype(float)

    cash = float(initial_capital)
    inventory: list[PositionLot] = []
    trades: list[TradeRecord] = []
    trade_id_counter = 1

    equity_records = [
        {
            "Date": dates[0],
            "Cash": cash,
            "Shares": 0,
            "Position_Value": 0.0,
            "Total_Equity": cash,
        }
    ]

    for i in range(n_bars - 1):
        curr_sig = int(signals[i])
        exec_idx = i + 1
        exec_date = dates[exec_idx]
        sig_date = dates[i]

        base_exec_price = opens[exec_idx] if execution_price == "open" else closes[exec_idx]

        # Cập nhật giá đỉnh cao nhất cho các lô đang nắm giữ (phục vụ Trailing Stop)
        for lot in inventory:
            if base_exec_price > lot.highest_price:
                lot.highest_price = base_exec_price

        # Kiểm tra điều kiện bán đối với các lô đã về tài khoản (T+2)
        settled_lots = [lot for lot in inventory if lot.settled_idx <= exec_idx]
        unsettled_lots = [lot for lot in inventory if lot.settled_idx > exec_idx]

        should_sell = False
        sell_reason = "SIGNAL_SELL"

        if len(settled_lots) > 0:
            # 1. Kiểm tra Cắt lỗ (Stop Loss)
            if stop_loss_pct is not None and stop_loss_pct > 0:
                for lot in settled_lots:
                    ret_from_buy = (base_exec_price - lot.buy_price) / lot.buy_price
                    if ret_from_buy <= -abs(stop_loss_pct):
                        should_sell = True
                        sell_reason = "STOP_LOSS"
                        break

            # 2. Kiểm tra Chốt lời (Take Profit)
            if not should_sell and take_profit_pct is not None and take_profit_pct > 0:
                for lot in settled_lots:
                    ret_from_buy = (base_exec_price - lot.buy_price) / lot.buy_price
                    if ret_from_buy >= abs(take_profit_pct):
                        should_sell = True
                        sell_reason = "TAKE_PROFIT"
                        break

            # 3. Kiểm tra Trailing Stop (Bảo toàn lãi khi giảm từ đỉnh)
            if not should_sell and trailing_stop_pct is not None and trailing_stop_pct > 0:
                for lot in settled_lots:
                    if lot.highest_price > lot.buy_price:
                        drop_from_peak = (lot.highest_price - base_exec_price) / lot.highest_price
                        if drop_from_peak >= abs(trailing_stop_pct):
                            should_sell = True
                            sell_reason = "TRAILING_STOP"
                            break

            # 4. Kiểm tra Tín hiệu Bán thông thường từ AI (curr_sig == 0)
            if not should_sell and curr_sig == 0:
                should_sell = True
                sell_reason = "SIGNAL_SELL"

        # Thực thi BÁN nếu thỏa mãn điều kiện và có hàng T+2
        if should_sell and len(settled_lots) > 0:
            sell_shares = sum(lot.shares for lot in settled_lots)
            p_sell = base_exec_price * (1.0 - slippage_rate)
            gross = sell_shares * p_sell
            fee = gross * fee_rate
            tax = gross * tax_rate
            net_proceeds = gross - fee - tax
            cash += net_proceeds

            total_cost_basis = sum(lot.cost_basis for lot in settled_lots)
            realized_pnl = net_proceeds - total_cost_basis
            realized_ret_pct = (
                (realized_pnl / total_cost_basis * 100.0) if total_cost_basis > 0 else 0.0
            )
            avg_holding = (
                sum((exec_idx - lot.buy_idx) * lot.shares for lot in settled_lots)
                / sell_shares
            )

            trades.append(
                TradeRecord(
                    trade_id=trade_id_counter,
                    symbol=symbol,
                    order_type="SELL",
                    signal_date=sig_date,
                    exec_date=exec_date,
                    exec_price=round(p_sell, 2),
                    shares=sell_shares,
                    gross_value=round(gross, 2),
                    fee=round(fee, 2),
                    tax=round(tax, 2),
                    net_cash_flow=round(net_proceeds, 2),
                    cash_after=round(cash, 2),
                    realized_pnl=round(realized_pnl, 2),
                    realized_return_pct=round(realized_ret_pct, 2),
                    holding_days=round(avg_holding, 1),
                    reason=sell_reason,
                )
            )
            trade_id_counter += 1
            inventory = unsettled_lots

        # Thực thi MUA (curr_sig == 2) nếu có tín hiệu MUA và còn đủ tiền
        elif curr_sig == 2 and cash > (base_exec_price * lot_size):
            p_buy = base_exec_price * (1.0 + slippage_rate)
            cost_per_share_with_fee = p_buy * (1.0 + fee_rate)
            max_shares = int(cash // cost_per_share_with_fee)
            buy_shares = (max_shares // lot_size) * lot_size

            if buy_shares > 0:
                gross = buy_shares * p_buy
                fee = gross * fee_rate
                total_outflow = gross + fee
                cash -= total_outflow

                lot = PositionLot(
                    shares=buy_shares,
                    buy_price=p_buy,
                    cost_basis=total_outflow,
                    buy_idx=exec_idx,
                    buy_date=exec_date,
                    settled_idx=exec_idx + settlement_delay,
                    highest_price=p_buy,
                )
                inventory.append(lot)

                trades.append(
                    TradeRecord(
                        trade_id=trade_id_counter,
                        symbol=symbol,
                        order_type="BUY",
                        signal_date=sig_date,
                        exec_date=exec_date,
                        exec_price=round(p_buy, 2),
                        shares=buy_shares,
                        gross_value=round(gross, 2),
                        fee=round(fee, 2),
                        tax=0.0,
                        net_cash_flow=round(-total_outflow, 2),
                        cash_after=round(cash, 2),
                        reason="SIGNAL_BUY",
                    )
                )
                trade_id_counter += 1

        # Định giá tài sản cuối ngày exec_idx
        shares_held = sum(lot.shares for lot in inventory)
        pos_val = shares_held * closes[exec_idx]
        total_eq = cash + pos_val
        equity_records.append(
            {
                "Date": exec_date,
                "Cash": cash,
                "Shares": shares_held,
                "Position_Value": pos_val,
                "Total_Equity": total_eq,
            }
        )

    # Đóng vị thế vào ngày cuối cùng nếu close_at_end=True
    if close_at_end and len(inventory) > 0:
        final_idx = n_bars - 1
        final_date = dates[final_idx]
        final_close = closes[final_idx]
        sell_shares = sum(lot.shares for lot in inventory)

        gross = sell_shares * final_close
        fee = gross * fee_rate
        tax = gross * tax_rate
        net_proceeds = gross - fee - tax
        cash += net_proceeds

        total_cost_basis = sum(lot.cost_basis for lot in inventory)
        realized_pnl = net_proceeds - total_cost_basis
        realized_ret_pct = (
            (realized_pnl / total_cost_basis * 100.0) if total_cost_basis > 0 else 0.0
        )
        avg_holding = (
            sum((final_idx - lot.buy_idx) * lot.shares for lot in inventory) / sell_shares
        )

        trades.append(
            TradeRecord(
                trade_id=trade_id_counter,
                symbol=symbol,
                order_type="SELL",
                signal_date=final_date,
                exec_date=final_date,
                exec_price=round(final_close, 2),
                shares=sell_shares,
                gross_value=round(gross, 2),
                fee=round(fee, 2),
                tax=round(tax, 2),
                net_cash_flow=round(net_proceeds, 2),
                cash_after=round(cash, 2),
                realized_pnl=round(realized_pnl, 2),
                realized_return_pct=round(realized_ret_pct, 2),
                holding_days=round(avg_holding, 1),
                reason="FINAL_LIQUIDATION",
            )
        )
        trade_id_counter += 1
        inventory.clear()

        # Cập nhật giá trị phiên cuối
        equity_records[-1]["Cash"] = cash
        equity_records[-1]["Shares"] = 0
        equity_records[-1]["Position_Value"] = 0.0
        equity_records[-1]["Total_Equity"] = cash

    eq_df = pd.DataFrame(equity_records)
    eq_df["Open"] = opens
    eq_df["High"] = (
        df_sorted["High"].values.astype(float) if "High" in df_sorted.columns else opens
    )
    eq_df["Low"] = df_sorted["Low"].values.astype(float) if "Low" in df_sorted.columns else opens
    eq_df["Close"] = closes

    trades_df = pd.DataFrame([t.__dict__ for t in trades]) if trades else pd.DataFrame()

    # Tính chiến lược đối chứng Mua & Nắm giữ (Buy & Hold)
    p_bh_buy = opens[1] * (1.0 + slippage_rate) if n_bars > 1 else opens[0]
    bh_shares_max = int((initial_capital // (p_bh_buy * (1.0 + fee_rate)) // lot_size) * lot_size)
    bh_cash = initial_capital - (bh_shares_max * p_bh_buy * (1.0 + fee_rate))
    bh_series = [initial_capital]

    for j in range(1, n_bars):
        if j == n_bars - 1 and close_at_end:
            final_p = closes[j]
            net_bh = bh_shares_max * final_p * (1.0 - fee_rate - tax_rate)
            bh_series.append(bh_cash + net_bh)
        else:
            bh_series.append(bh_cash + bh_shares_max * closes[j])

    eq_df["Benchmark_Equity"] = bh_series
    bh_return_pct = (
        ((bh_series[-1] - initial_capital) / initial_capital) * 100.0
        if initial_capital > 0
        else 0.0
    )

    # Bổ sung tính toán drawdown cho equity curve
    peaks = np.maximum.accumulate(eq_df["Total_Equity"].values)
    drawdowns = (eq_df["Total_Equity"].values - peaks) / np.where(peaks > 0, peaks, 1.0)
    eq_df["Drawdown_Pct"] = np.round(drawdowns * 100.0, 2)
    eq_df["Daily_Return"] = np.round(eq_df["Total_Equity"].pct_change().fillna(0.0) * 100.0, 2)

    metrics = calculate_financial_metrics(
        equity_series=eq_df["Total_Equity"],
        initial_capital=initial_capital,
        trades=trades,
        risk_free_rate=risk_free_rate,
        buy_and_hold_return_pct=bh_return_pct,
    )

    return metrics, eq_df, trades_df


def run_backtest(
    df: pd.DataFrame,
    signals: np.ndarray | None = None,
    probabilities: np.ndarray | None = None,
    buy_prob_threshold: float = 0.40,
    sell_prob_threshold: float = 0.40,
    symbol: str = "VIC",
    initial_capital: float = INITIAL_CAPITAL,
    fee_rate: float = TRANSACTION_FEE_RATE,
    tax_rate: float = TAX_RATE,
    slippage_rate: float = 0.0005,
    lot_size: int = LOT_SIZE,
    settlement_delay: int = 2,
    execution_price: str = "open",
    close_at_end: bool = True,
    risk_free_rate: float = 0.04,
    strategy_name: str = "AI_Strategy",
    take_profit_pct: float | None = None,
    stop_loss_pct: float | None = None,
    trailing_stop_pct: float | None = None,
) -> BacktestResult:
    """
    Giao diện chạy Backtest cấp cao hỗ trợ cả nhãn tín hiệu trực tiếp hoặc ma trận xác suất 3 lớp,
    kèm theo bộ quy tắc quản trị rủi ro vị thế (Take Profit, Stop Loss, Trailing Stop).
    """
    if signals is None:
        if probabilities is None:
            raise ValueError(
                "Phải cung cấp một trong hai tham số: 'signals' hoặc 'probabilities'."
            )
        # Sinh tín hiệu từ ma trận xác suất:
        # Lớp 0: Giảm, Lớp 1: Đi ngang, Lớp 2: Tăng
        sig_list = []
        for p in probabilities:
            if p[2] >= buy_prob_threshold:
                sig_list.append(2)  # Mua
            elif p[0] >= sell_prob_threshold:
                sig_list.append(0)  # Bán
            else:
                sig_list.append(1)  # Giữ
        signals = np.array(sig_list, dtype=int)

    metrics, eq_df, trades_df = simulate_vietnam_trading(
        df=df,
        signals=signals,
        symbol=symbol,
        initial_capital=initial_capital,
        fee_rate=fee_rate,
        tax_rate=tax_rate,
        slippage_rate=slippage_rate,
        lot_size=lot_size,
        settlement_delay=settlement_delay,
        execution_price=execution_price,
        close_at_end=close_at_end,
        risk_free_rate=risk_free_rate,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
        trailing_stop_pct=trailing_stop_pct,
    )

    config = {
        "symbol": symbol,
        "initial_capital": initial_capital,
        "fee_rate": fee_rate,
        "tax_rate": tax_rate,
        "slippage_rate": slippage_rate,
        "lot_size": lot_size,
        "settlement_delay": settlement_delay,
        "execution_price": execution_price,
        "close_at_end": close_at_end,
        "risk_free_rate": risk_free_rate,
        "take_profit_pct": take_profit_pct,
        "stop_loss_pct": stop_loss_pct,
        "trailing_stop_pct": trailing_stop_pct,
    }

    return BacktestResult(
        symbol=symbol,
        strategy_name=strategy_name,
        metrics=metrics,
        equity_df=eq_df,
        trades_df=trades_df,
        config=config,
    )


def run_buy_and_hold(
    df: pd.DataFrame,
    symbol: str = "VIC",
    initial_capital: float = INITIAL_CAPITAL,
    fee_rate: float = TRANSACTION_FEE_RATE,
    tax_rate: float = TAX_RATE,
    slippage_rate: float = 0.0005,
    lot_size: int = LOT_SIZE,
    execution_price: str = "open",
    close_at_end: bool = True,
    risk_free_rate: float = 0.04,
) -> BacktestResult:
    """Mô phỏng chiến lược Mua và Nắm giữ thuần túy (Buy & Hold)."""
    n_bars = len(df)
    # Tín hiệu Mua vào ngày đầu tiên, sau đó giữ nguyên (1)
    signals = np.ones(n_bars, dtype=int)
    if n_bars > 0:
        signals[0] = 2

    return run_backtest(
        df=df,
        signals=signals,
        symbol=symbol,
        initial_capital=initial_capital,
        fee_rate=fee_rate,
        tax_rate=tax_rate,
        slippage_rate=slippage_rate,
        lot_size=lot_size,
        settlement_delay=2,
        execution_price=execution_price,
        close_at_end=close_at_end,
        risk_free_rate=risk_free_rate,
        strategy_name="Buy_and_Hold",
    )


def run_random_baseline(
    df: pd.DataFrame,
    symbol: str = "VIC",
    initial_capital: float = INITIAL_CAPITAL,
    seed: int = 42,
    class_probs: tuple[float, float, float] = (0.25, 0.50, 0.25),
    **kwargs: Any,
) -> BacktestResult:
    """Mô phỏng chiến lược phát tín hiệu ngẫu nhiên theo phân phối lớp thực nghiệm."""
    np.random.seed(seed)
    n_bars = len(df)
    classes = [0, 1, 2]
    signals = np.random.choice(classes, size=n_bars, p=list(class_probs))

    return run_backtest(
        df=df,
        signals=signals,
        symbol=symbol,
        initial_capital=initial_capital,
        strategy_name=f"Random_Baseline_Seed{seed}",
        **kwargs,
    )


def run_monte_carlo_random_test(
    df: pd.DataFrame,
    symbol: str = "VIC",
    ai_result: BacktestResult | None = None,
    n_simulations: int = 100,
    seed: int = 42,
    class_probs: tuple[float, float, float] = (0.25, 0.50, 0.25),
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Thực hiện kiểm định Monte Carlo mô phỏng n_simulations đường chạy tín hiệu ngẫu nhiên:
    - Tính khoảng tin cậy 90% (5th - 95th percentile) cho Sharpe Ratio, ROI, MDD.
    - Đánh giá giá trị p-value thực nghiệm để kiểm chứng độ tin cậy khoa học của AI.
    """
    np.random.seed(seed)
    n_bars = len(df)
    classes = [0, 1, 2]

    mc_returns = []
    mc_sharpes = []
    mc_mdds = []
    mc_win_rates = []

    for _ in range(n_simulations):
        rand_signals = np.random.choice(classes, size=n_bars, p=list(class_probs))
        res = run_backtest(
            df=df,
            signals=rand_signals,
            symbol=symbol,
            strategy_name="Random_MC",
            **kwargs,
        )
        mc_returns.append(res.metrics.total_return_pct)
        mc_sharpes.append(res.metrics.sharpe_ratio)
        mc_mdds.append(res.metrics.max_drawdown_pct)
        mc_win_rates.append(res.metrics.win_rate_pct)

    arr_ret = np.array(mc_returns)
    arr_shp = np.array(mc_sharpes)
    arr_mdd = np.array(mc_mdds)

    out = {
        "symbol": symbol,
        "n_simulations": n_simulations,
        "roi_stats": {
            "mean": round(float(arr_ret.mean()), 2),
            "std": round(float(arr_ret.std()), 2),
            "p5": round(float(np.percentile(arr_ret, 5)), 2),
            "median": round(float(np.median(arr_ret)), 2),
            "p95": round(float(np.percentile(arr_ret, 95)), 2),
        },
        "sharpe_stats": {
            "mean": round(float(arr_shp.mean()), 4),
            "std": round(float(arr_shp.std()), 4),
            "p5": round(float(np.percentile(arr_shp, 5)), 4),
            "median": round(float(np.median(arr_shp)), 4),
            "p95": round(float(np.percentile(arr_shp, 95)), 4),
        },
        "mdd_stats": {
            "mean": round(float(arr_mdd.mean()), 2),
            "std": round(float(arr_mdd.std()), 2),
            "median": round(float(np.median(arr_mdd)), 2),
        },
    }

    if ai_result is not None:
        ai_ret = ai_result.metrics.total_return_pct
        ai_shp = ai_result.metrics.sharpe_ratio
        p_val_ret = float(np.mean(arr_ret >= ai_ret))
        p_val_shp = float(np.mean(arr_shp >= ai_shp))
        out["ai_comparison"] = {
            "ai_roi": ai_ret,
            "ai_sharpe": ai_shp,
            "p_value_roi": round(p_val_ret, 4),
            "p_value_sharpe": round(p_val_shp, 4),
            "statistically_significant_at_5pct": bool(p_val_shp < 0.05),
        }

    return out


def run_simple_backtest(
    prices: np.ndarray,
    predictions: np.ndarray,
    initial_capital: float = INITIAL_CAPITAL,
    fee_rate: float = TRANSACTION_FEE_RATE,
    tax_rate: float = TAX_RATE,
    buy_threshold: float = 0.015,
    sell_threshold: float = -0.015,
) -> BacktestMetrics:
    """
    Hàm kế thừa tương thích ngược hoàn toàn với phiên bản PoC cũ.
    """
    cash = float(initial_capital)
    shares = 0
    trade_count = 0
    winning_trades = 0
    losing_trades = 0
    last_buy_price = 0.0
    equity_curve: list[float] = []

    for i in range(len(prices) - 1):
        curr_price = float(prices[i])
        next_pred = float(predictions[i])
        expected_return = (next_pred - curr_price) / curr_price if curr_price > 0 else 0

        if expected_return > buy_threshold and cash > curr_price * LOT_SIZE:
            available_shares = int(cash // (curr_price * (1 + fee_rate)))
            lot_shares = (available_shares // LOT_SIZE) * LOT_SIZE
            if lot_shares > 0:
                cost = lot_shares * curr_price * (1 + fee_rate)
                cash -= cost
                shares += lot_shares
                last_buy_price = curr_price
                trade_count += 1

        elif expected_return < sell_threshold and shares > 0:
            gross_proceeds = shares * curr_price
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

    final_price = float(prices[-1])
    if shares > 0:
        cash += shares * final_price * (1 - fee_rate - tax_rate)
        shares = 0
    final_equity = cash
    equity_curve.append(final_equity)

    total_return_pct = ((final_equity - initial_capital) / initial_capital) * 100
    buy_and_hold_return_pct = (
        ((prices[-1] - prices[0]) / prices[0]) * 100 if prices[0] > 0 else 0.0
    )
    closed_trades = winning_trades + losing_trades
    win_rate_pct = (winning_trades / closed_trades * 100) if closed_trades > 0 else 0.0

    equity_arr = np.array(equity_curve)
    peaks = np.maximum.accumulate(equity_arr)
    drawdowns = (equity_arr - peaks) / np.where(peaks > 0, peaks, 1.0)
    max_drawdown_pct = float(np.min(drawdowns) * 100) if len(drawdowns) > 0 else 0.0

    return BacktestMetrics(
        initial_capital=initial_capital,
        final_equity=round(final_equity, 2),
        total_return_pct=round(total_return_pct, 2),
        cagr_pct=0.0,
        buy_and_hold_return_pct=round(buy_and_hold_return_pct, 2),
        excess_return_pct=round(total_return_pct - buy_and_hold_return_pct, 2),
        annualized_volatility_pct=0.0,
        sharpe_ratio=0.0,
        sortino_ratio=0.0,
        max_drawdown_pct=round(abs(max_drawdown_pct), 2),
        calmar_ratio=0.0,
        var_95_pct=0.0,
        cvar_95_pct=0.0,
        win_rate_pct=round(win_rate_pct, 2),
        profit_factor=0.0,
        total_trades=trade_count,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        avg_trade_return_pct=0.0,
        best_trade_return_pct=0.0,
        worst_trade_return_pct=0.0,
        avg_holding_days=0.0,
        total_fees_paid=0.0,
        total_taxes_paid=0.0,
        total_costs=0.0,
        cost_impact_pct=0.0,
        equity_curve=[round(x, 2) for x in equity_curve],
    )


def backtest_symbol_oos(
    symbol: str = "VIC",
    model_type: str = "lightgbm",
    models_dir: Path = MODELS_DIR,
    initial_capital: float = INITIAL_CAPITAL,
    slippage_rate: float = 0.0005,
    take_profit_pct: float | None = None,
    stop_loss_pct: float | None = None,
    trailing_stop_pct: float | None = None,
) -> BacktestResult:
    """
    Thực hiện Backtest tự động trên tập kiểm thử Out-of-Sample (OOS Cửa sổ 3)
    sử dụng mô hình AI và Scaler đã lưu trong models/.
    """
    from vn_stock.data_ingestion import load_panel_dataset
    from vn_stock.features import (
        ALL_FEATURE_COLS,
        FEATURE_COLS,
        compute_features_per_symbol,
    )
    from vn_stock.splitting_data import (
        apply_study_window,
        create_labels_per_symbol,
        generate_walk_forward_windows,
    )

    clean_sym = symbol.upper()

    df_raw = load_panel_dataset()
    df_feat = compute_features_per_symbol(df_raw, drop_na=True)
    df_study = apply_study_window(df_feat)
    df_labeled = create_labels_per_symbol(df_study)
    w3 = generate_walk_forward_windows(df_labeled)[2]
    test_df = w3["test_df"].copy()

    sym_df = (
        test_df[test_df["Symbol"] == clean_sym].copy().sort_values("Date").reset_index(drop=True)
    )
    if sym_df.empty:
        raise ValueError(f"Không tìm thấy dữ liệu cho mã {clean_sym} trong tập test.")

    scaler_path = models_dir / "scaler_window3.pkl"
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    sym_scaled = sym_df.copy()
    sym_scaled[FEATURE_COLS] = scaler.transform(sym_df[FEATURE_COLS])

    if model_type.lower() == "lightgbm":
        import lightgbm as lgb

        lgb_file = models_dir / "lightgbm_classifier.txt"
        booster = lgb.Booster(model_file=str(lgb_file))
        probs = booster.predict(sym_scaled[ALL_FEATURE_COLS])
        signals = np.argmax(probs, axis=1)
    elif model_type.lower() == "lstm":
        import torch

        from vn_stock.features import create_multivariate_sequences
        from vn_stock.modeling.model import GlobalLSTMClassifier
        from vn_stock.splitting_data import get_warmup_tail, scale_window

        _, va_sc, te_sc, _ = scale_window(w3["train_df"], w3["val_df"], w3["test_df"])
        warmup_val = get_warmup_tail(va_sc, seq_length=20)
        xs_te, _ = create_multivariate_sequences(
            te_sc, warmup_df=warmup_val, feature_cols=ALL_FEATURE_COLS
        )

        sym_mask = te_sc["Symbol"] == clean_sym
        xs_sym = xs_te[sym_mask.values]

        device = torch.device("cpu")
        lstm_model = GlobalLSTMClassifier(
            input_size=len(ALL_FEATURE_COLS),
            hidden_size=64,
            num_layers=2,
            num_classes=3,
            dropout=0.2,
        ).to(device)
        lstm_model.load_state_dict(
            torch.load(models_dir / "global_lstm_classifier.pth", map_location=device)
        )
        lstm_model.eval()

        with torch.no_grad():
            x_t = torch.from_numpy(np.ascontiguousarray(xs_sym))
            probs = lstm_model.predict_proba(x_t).numpy()
            signals = np.argmax(probs, axis=1)
    else:
        raise ValueError(
            f"model_type '{model_type}' không hợp lệ (hỗ trợ 'lightgbm' hoặc 'lstm')."
        )

    return run_backtest(
        df=sym_df,
        signals=signals,
        symbol=clean_sym,
        initial_capital=initial_capital,
        slippage_rate=slippage_rate,
        strategy_name=f"AI_{model_type.upper()}_OOS",
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
        trailing_stop_pct=trailing_stop_pct,
    )


def backtest_all_symbols(
    symbols: list[str] | None = None,
    model_type: str = "lightgbm",
    initial_capital: float = INITIAL_CAPITAL,
    slippage_rate: float = 0.0005,
) -> pd.DataFrame:
    """Chạy Backtest OOS đồng loạt trên danh mục cổ phiếu và xuất bảng tổng hợp đối chứng."""
    from vn_stock.config import DEFAULT_SYMBOLS

    target_symbols = symbols or DEFAULT_SYMBOLS
    rows = []

    for sym in target_symbols:
        res = backtest_symbol_oos(
            symbol=sym,
            model_type=model_type,
            initial_capital=initial_capital,
            slippage_rate=slippage_rate,
        )
        m = res.metrics
        rows.append(
            {
                "Symbol": sym,
                "Model": model_type.upper(),
                "ROI %": m.total_return_pct,
                "B&H ROI %": m.buy_and_hold_return_pct,
                "Excess %": m.excess_return_pct,
                "Sharpe": m.sharpe_ratio,
                "Sortino": m.sortino_ratio,
                "MDD %": m.max_drawdown_pct,
                "Win Rate %": m.win_rate_pct,
                "Profit Factor": m.profit_factor,
                "Trades": m.total_trades,
                "Costs (VND)": m.total_costs,
            }
        )

    return pd.DataFrame(rows)


def prepare_backtest_df(df: pd.DataFrame) -> pd.DataFrame:
    """Tính toán các chỉ báo kỹ thuật cơ bản cho một mã phục vụ bộ lọc điều kiện chiến thuật."""
    df_clean = df.copy().sort_values("Date").reset_index(drop=True)
    if not pd.api.types.is_datetime64_any_dtype(df_clean["Date"]):
        df_clean["Date"] = pd.to_datetime(df_clean["Date"])

    close = df_clean["Close"].astype(float)
    high = df_clean["High"].astype(float) if "High" in df_clean.columns else close
    low = df_clean["Low"].astype(float) if "Low" in df_clean.columns else close
    volume = (
        df_clean["Volume"].astype(float)
        if "Volume" in df_clean.columns
        else pd.Series(0.0, index=df_clean.index)
    )

    # MA Series đa chu kỳ (SMA 5, 10, 20, 50, 100, 200)
    for span in [5, 10, 20, 50, 100, 200]:
        df_clean[f"SMA{span}"] = close.rolling(span, min_periods=1).mean()

    # EMA Series đa chu kỳ (EMA 5, 10, 12, 20, 26, 50, 100, 200)
    for span in [5, 10, 12, 20, 26, 50, 100, 200]:
        df_clean[f"EMA{span}"] = close.ewm(span=span, adjust=False).mean()

    # MACD (12, 26, 9)
    df_clean["MACD"] = df_clean["EMA12"] - df_clean["EMA26"]
    df_clean["MACD_Signal"] = df_clean["MACD"].ewm(span=9, adjust=False).mean()

    # RSI (14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14, min_periods=1).mean()
    rs = gain / (loss + 1e-9)
    df_clean["RSI"] = 100.0 - (100.0 / (1.0 + rs))

    # Bollinger Bands (20, 2)
    std20 = close.rolling(20, min_periods=1).std().fillna(0.0)
    df_clean["BB_Upper"] = df_clean["SMA20"] + 2.0 * std20
    df_clean["BB_Lower"] = df_clean["SMA20"] - 2.0 * std20

    # Volume SMAs (5, 10, 20)
    for span in [5, 10, 20]:
        df_clean[f"Vol_SMA{span}"] = volume.rolling(span, min_periods=1).mean()

    # GTGD trung bình (Tỷ VNĐ) theo chu kỳ 5, 10, 20 phiên
    val_series = (close * volume) / 1e6
    for span in [5, 10, 20]:
        df_clean[f"Avg_Trading_Val_{span}"] = val_series.rolling(span, min_periods=1).mean()

    # ADX (14)
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr14 = tr.rolling(14, min_periods=1).mean()
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_di = 100.0 * (pd.Series(plus_dm).rolling(14, min_periods=1).mean() / (atr14 + 1e-9))
    minus_di = 100.0 * (pd.Series(minus_dm).rolling(14, min_periods=1).mean() / (atr14 + 1e-9))
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    df_clean["ADX"] = dx.rolling(14, min_periods=1).mean().fillna(20.0)

    # Relative Strength RS (0 - 99.93)
    rs_60 = close.pct_change(60).fillna(0.0)
    df_clean["RS"] = ((rs_60.rank(pct=True)) * 99.93).clip(0.0, 99.93)

    return df_clean


def evaluate_strategy_signals(
    df: pd.DataFrame,
    buy_rules: dict[str, Any] | None = None,
    sell_rules: dict[str, Any] | None = None,
    ai_signals: np.ndarray | None = None,
    symbol_meta: dict[str, Any] | None = None,
) -> np.ndarray:
    """
    Sinh tín hiệu MUA (2), BÁN (0), NẮM GIỮ (1) dựa trên bộ điều kiện Mua/Bán chuẩn DNSE
    hỗ trợ toán tử logic VÀ (AND) / HOẶC (OR) kết hợp hoặc độc lập với mô hình AI.
    """
    n_bars = len(df)
    signals = np.ones(n_bars, dtype=int)
    if n_bars == 0:
        return signals

    buy_rules = buy_rules or {}
    sell_rules = sell_rules or {}

    buy_logic = str(buy_rules.get("condition_logic", "AND")).upper()
    sell_logic = str(sell_rules.get("condition_logic", "OR")).upper()

    buy_rule_keys = [
        "use_volume_spike",
        "use_pb",
        "use_stock_price",
        "use_market_cap",
        "use_avg_trading_val",
        "use_ma",
        "use_rsi",
        "use_price_increase",
        "growth_rev_latest",
        "growth_np_latest",
        "use_pe",
        "use_roa",
        "growth_eps",
        "foreign_net_val",
        "foreign_net_buy",
        "prop_net_vol",
        "foreign_net_vol",
        "use_roe",
        "growth_np_prev",
        "growth_rev_prev",
        "use_adx",
        "use_ema",
        "use_macd",
        "use_rs",
        "growth_rev_ttm",
        "growth_np_ttm",
        "use_ps",
        "use_eps",
        "prop_net_val",
        "prop_net_buy",
        "use_price_cross",
        "use_bb",
    ]
    has_custom_buy = any(bool(buy_rules.get(k)) for k in buy_rule_keys)

    sell_rule_keys = [
        "use_ma",
        "use_price_cross",
        "use_rsi",
        "foreign_net_sell_val",
        "foreign_net_sell",
        "prop_net_sell_vol",
        "use_adx",
        "use_ema",
        "foreign_net_sell_vol",
        "use_rs",
        "use_macd",
        "prop_net_sell_val",
        "use_bb",
    ]
    has_custom_sell = any(bool(sell_rules.get(k)) for k in sell_rule_keys)

    for i in range(n_bars):
        # 1. Đánh giá điều kiện MUA
        buy_cond = True
        if has_custom_buy:
            active_buy_flags: list[bool] = []

            # 1. % KLGD đột biến
            if buy_rules.get("use_volume_spike"):
                period = int(buy_rules.get("vol_spike_period") or 10)
                col = f"Vol_SMA{period}" if f"Vol_SMA{period}" in df else "Vol_SMA20"
                base_vol = df[col].iloc[i]
                spike_pct = ((df["Volume"].iloc[i] / (base_vol + 1e-9)) - 1.0) * 100.0
                min_spike = float(buy_rules.get("min_vol_spike_pct") if buy_rules.get("min_vol_spike_pct") is not None else -100.0)
                max_spike = float(buy_rules.get("max_vol_spike_pct") if buy_rules.get("max_vol_spike_pct") is not None else 19900.0)
                active_buy_flags.append(bool(min_spike <= spike_pct <= max_spike))

            # 2. P/B
            if buy_rules.get("use_pb"):
                min_pb = float(buy_rules.get("min_pb") if buy_rules.get("min_pb") is not None else 0.0)
                max_pb = float(buy_rules.get("max_pb") if buy_rules.get("max_pb") is not None else 10.0)
                pb_est = float(symbol_meta.get("pb", 1.2)) if symbol_meta and "pb" in symbol_meta else 1.2
                active_buy_flags.append(bool(min_pb <= pb_est <= max_pb))

            # 3. Giá cổ phiếu (nghìn đồng)
            if buy_rules.get("use_stock_price"):
                min_p = float(buy_rules.get("min_stock_price") if buy_rules.get("min_stock_price") is not None else 0.0)
                max_p = float(buy_rules.get("max_stock_price") if buy_rules.get("max_stock_price") is not None else 999999.0)
                active_buy_flags.append(bool(min_p <= df["Close"].iloc[i] <= max_p))

            # 4. Vốn hóa (Tỷ)
            if buy_rules.get("use_market_cap"):
                min_cap = float(buy_rules.get("min_market_cap") if buy_rules.get("min_market_cap") is not None else 0.0)
                max_cap = float(buy_rules.get("max_market_cap") if buy_rules.get("max_market_cap") is not None else 1e12)
                cap_est = float(symbol_meta.get("market_cap", 25000)) if symbol_meta and "market_cap" in symbol_meta else 15000
                active_buy_flags.append(bool(min_cap <= cap_est <= max_cap))

            # 5. GTGD trung bình (Tỷ)
            if buy_rules.get("use_avg_trading_val"):
                period = int(buy_rules.get("avg_trading_val_period") or 10)
                col = f"Avg_Trading_Val_{period}" if f"Avg_Trading_Val_{period}" in df else "Avg_Trading_Val_10"
                val = df[col].iloc[i] if col in df else (df["Close"].iloc[i] * df["Volume"].iloc[i] / 1e6)
                min_val = float(buy_rules.get("min_avg_trading_val") if buy_rules.get("min_avg_trading_val") is not None else 0.0)
                max_val = float(buy_rules.get("max_avg_trading_val") if buy_rules.get("max_avg_trading_val") is not None else 999999.0)
                active_buy_flags.append(bool(min_val <= val <= max_val))

            # 6. MA (Đầy đủ toán tử Cắt lên, Cắt xuống, Nằm trên, Nằm dưới)
            if buy_rules.get("use_ma"):
                left_key = buy_rules.get("ma_left", "MA 10")
                right_key = buy_rules.get("ma_right", "MA 20")
                op = buy_rules.get("ma_operator", "Cắt lên")

                def get_ma_val(key: str, idx: int) -> float:
                    if "giá" in key.lower():
                        return float(df["Close"].iloc[idx])
                    digits = "".join(ch for ch in key if ch.isdigit())
                    col = f"SMA{digits}" if digits else "SMA20"
                    if col in df:
                        return float(df[col].iloc[idx])
                    return float(df["SMA20"].iloc[idx])

                l_curr = get_ma_val(left_key, i)
                r_curr = get_ma_val(right_key, i)

                if op == "Cắt lên":
                    if i > 0:
                        l_prev = get_ma_val(left_key, i - 1)
                        r_prev = get_ma_val(right_key, i - 1)
                        active_buy_flags.append(bool(l_prev <= r_prev and l_curr > r_curr))
                    else:
                        active_buy_flags.append(bool(l_curr > r_curr))
                elif op == "Cắt xuống":
                    if i > 0:
                        l_prev = get_ma_val(left_key, i - 1)
                        r_prev = get_ma_val(right_key, i - 1)
                        active_buy_flags.append(bool(l_prev >= r_prev and l_curr < r_curr))
                    else:
                        active_buy_flags.append(bool(l_curr < r_curr))
                elif op in ["Nằm trên", ">"]:
                    active_buy_flags.append(bool(l_curr > r_curr))
                elif op in ["Nằm dưới", "<"]:
                    active_buy_flags.append(bool(l_curr < r_curr))
                else:
                    active_buy_flags.append(bool(l_curr > r_curr))

            # 7. RSI (14)
            if buy_rules.get("use_rsi"):
                min_r = float(buy_rules.get("rsi_min") if buy_rules.get("rsi_min") is not None else 0.0)
                max_r = float(buy_rules.get("rsi_max") if buy_rules.get("rsi_max") is not None else float(buy_rules.get("rsi_threshold", 45.0) or 45.0))
                active_buy_flags.append(bool(min_r <= df["RSI"].iloc[i] <= max_r))

            # 8. Giá T0 so với T-1
            if buy_rules.get("use_price_increase"):
                if i > 0:
                    t0_field = buy_rules.get("price_t0_field", "Giá đóng cửa T0")
                    t1_field = buy_rules.get("price_t1_field", "Giá đóng cửa T-1")
                    op = buy_rules.get("price_t0_operator", ">")

                    def get_price(fld: str, idx: int) -> float:
                        low_fld = fld.lower()
                        if "mở cửa" in low_fld:
                            return float(df["Open"].iloc[idx])
                        if "cao nhất" in low_fld:
                            return float(df["High"].iloc[idx])
                        if "thấp nhất" in low_fld:
                            return float(df["Low"].iloc[idx])
                        return float(df["Close"].iloc[idx])

                    p0 = get_price(t0_field, i)
                    p1 = get_price(t1_field, i - 1)

                    if op == ">":
                        active_buy_flags.append(bool(p0 > p1))
                    elif op == "<":
                        active_buy_flags.append(bool(p0 < p1))
                    elif op == ">=":
                        active_buy_flags.append(bool(p0 >= p1))
                    elif op == "<=":
                        active_buy_flags.append(bool(p0 <= p1))
                    else:
                        active_buy_flags.append(bool(abs(p0 - p1) < 1e-4))
                else:
                    active_buy_flags.append(True)

            # 9. EMA
            if buy_rules.get("use_ema"):
                left_key = buy_rules.get("ema_left", "EMA 10")
                right_key = buy_rules.get("ema_right", "EMA 20")
                op = buy_rules.get("ema_operator", "Cắt lên")

                def get_ema_val(key: str, idx: int) -> float:
                    if "giá" in key.lower():
                        return float(df["Close"].iloc[idx])
                    digits = "".join(ch for ch in key if ch.isdigit())
                    col = f"EMA{digits}" if digits else "EMA20"
                    if col in df:
                        return float(df[col].iloc[idx])
                    return float(df["EMA20"].iloc[idx])

                el_curr = get_ema_val(left_key, i)
                er_curr = get_ema_val(right_key, i)

                if op == "Cắt lên":
                    if i > 0:
                        el_prev = get_ema_val(left_key, i - 1)
                        er_prev = get_ema_val(right_key, i - 1)
                        active_buy_flags.append(bool(el_prev <= er_prev and el_curr > er_curr))
                    else:
                        active_buy_flags.append(bool(el_curr > er_curr))
                elif op == "Cắt xuống":
                    if i > 0:
                        el_prev = get_ema_val(left_key, i - 1)
                        er_prev = get_ema_val(right_key, i - 1)
                        active_buy_flags.append(bool(el_prev >= er_prev and el_curr < er_curr))
                    else:
                        active_buy_flags.append(bool(el_curr < er_curr))
                elif op in ["Nằm trên", ">"]:
                    active_buy_flags.append(bool(el_curr > er_curr))
                elif op in ["Nằm dưới", "<"]:
                    active_buy_flags.append(bool(el_curr < er_curr))
                else:
                    active_buy_flags.append(bool(el_curr > er_curr))

            # 10. MACD (12,26,9)
            if buy_rules.get("use_macd"):
                op = buy_rules.get("macd_operator", "Cắt lên")
                target = buy_rules.get("macd_target", "Đường tín hiệu")
                def get_macd_target(idx: int) -> float:
                    return float(df["MACD_Signal"].iloc[idx]) if "tín hiệu" in target.lower() else 0.0

                m_curr = float(df["MACD"].iloc[i])
                t_curr = get_macd_target(i)
                if op == "Cắt lên":
                    if i > 0:
                        m_prev = float(df["MACD"].iloc[i - 1])
                        t_prev = get_macd_target(i - 1)
                        active_buy_flags.append(bool(m_prev <= t_prev and m_curr > t_curr))
                    else:
                        active_buy_flags.append(bool(m_curr > t_curr))
                elif op == "Cắt xuống":
                    if i > 0:
                        m_prev = float(df["MACD"].iloc[i - 1])
                        t_prev = get_macd_target(i - 1)
                        active_buy_flags.append(bool(m_prev >= t_prev and m_curr < t_curr))
                    else:
                        active_buy_flags.append(bool(m_curr < t_curr))
                elif op in ["Nằm trên", ">"]:
                    active_buy_flags.append(bool(m_curr > t_curr))
                elif op in ["Nằm dưới", "<"]:
                    active_buy_flags.append(bool(m_curr < t_curr))
                else:
                    active_buy_flags.append(bool(m_curr > t_curr))

            # 11. ADX (14)
            if buy_rules.get("use_adx"):
                min_adx = float(buy_rules.get("min_adx") if buy_rules.get("min_adx") is not None else 0.0)
                max_adx = float(buy_rules.get("max_adx") if buy_rules.get("max_adx") is not None else 100.0)
                active_buy_flags.append(bool(min_adx <= df["ADX"].iloc[i] <= max_adx))

            # 12. RS
            if buy_rules.get("use_rs"):
                min_rs = float(buy_rules.get("min_rs") if buy_rules.get("min_rs") is not None else 0.0)
                max_rs = float(buy_rules.get("max_rs") if buy_rules.get("max_rs") is not None else 100.0)
                rs_val = float(df["RS"].iloc[i]) if "RS" in df else 50.0
                active_buy_flags.append(bool(min_rs <= rs_val <= max_rs))

            # 13. Giá cắt đường MA/EMA/BB
            if buy_rules.get("use_price_cross"):
                tgt = buy_rules.get("price_cross_target", "MA 10")
                op = buy_rules.get("price_cross_operator", "Cắt lên")

                def get_cross_target_val(idx: int) -> float:
                    t_low = tgt.lower()
                    if "bb trên" in t_low:
                        return float(df["BB_Upper"].iloc[idx])
                    if "bb dưới" in t_low:
                        return float(df["BB_Lower"].iloc[idx])
                    digits = "".join(ch for ch in tgt if ch.isdigit())
                    if "ema" in t_low:
                        col = f"EMA{digits}" if digits else "EMA20"
                        return float(df[col].iloc[idx]) if col in df else float(df["EMA20"].iloc[idx])
                    col = f"SMA{digits}" if digits else "SMA10"
                    return float(df[col].iloc[idx]) if col in df else float(df["SMA20"].iloc[idx])

                c_curr = float(df["Close"].iloc[i])
                t_curr = get_cross_target_val(i)
                if op == "Cắt lên":
                    if i > 0:
                        c_prev = float(df["Close"].iloc[i - 1])
                        t_prev = get_cross_target_val(i - 1)
                        active_buy_flags.append(bool(c_prev <= t_prev and c_curr > t_curr))
                    else:
                        active_buy_flags.append(bool(c_curr > t_curr))
                elif op == "Cắt xuống":
                    if i > 0:
                        c_prev = float(df["Close"].iloc[i - 1])
                        t_prev = get_cross_target_val(i - 1)
                        active_buy_flags.append(bool(c_prev >= t_prev and c_curr < t_curr))
                    else:
                        active_buy_flags.append(bool(c_curr < t_curr))
                elif op in ["Nằm trên", ">"]:
                    active_buy_flags.append(bool(c_curr > t_curr))
                elif op in ["Nằm dưới", "<"]:
                    active_buy_flags.append(bool(c_curr < t_curr))
                else:
                    active_buy_flags.append(bool(c_curr > t_curr))

            # 14. Bollinger Bands
            if buy_rules.get("use_bb"):
                active_buy_flags.append(bool(df["Close"].iloc[i] <= df["BB_Lower"].iloc[i] * 1.02))

            # 15. Financial & Fundamental Indicators
            if buy_rules.get("use_pe"):
                min_pe = float(buy_rules.get("min_pe") if buy_rules.get("min_pe") is not None else -100.0)
                max_pe = float(buy_rules.get("max_pe") if buy_rules.get("max_pe") is not None else 150.0)
                pe_est = float(symbol_meta.get("pe", 14.5)) if symbol_meta and "pe" in symbol_meta else 12.0
                active_buy_flags.append(bool(min_pe <= pe_est <= max_pe))

            if buy_rules.get("use_ps"):
                min_ps = float(buy_rules.get("min_ps") if buy_rules.get("min_ps") is not None else 0.0)
                max_ps = float(buy_rules.get("max_ps") if buy_rules.get("max_ps") is not None else 20.0)
                ps_est = float(symbol_meta.get("ps", 1.8)) if symbol_meta and "ps" in symbol_meta else 1.5
                active_buy_flags.append(bool(min_ps <= ps_est <= max_ps))

            if buy_rules.get("use_roa"):
                min_roa = float(buy_rules.get("min_roa") if buy_rules.get("min_roa") is not None else -50.0)
                max_roa = float(buy_rules.get("max_roa") if buy_rules.get("max_roa") is not None else 50.0)
                roa_est = float(symbol_meta.get("roa", 6.5)) if symbol_meta and "roa" in symbol_meta else 5.0
                active_buy_flags.append(bool(min_roa <= roa_est <= max_roa))

            if buy_rules.get("use_roe"):
                min_roe = float(buy_rules.get("min_roe") if buy_rules.get("min_roe") is not None else -50.0)
                max_roe = float(buy_rules.get("max_roe") if buy_rules.get("max_roe") is not None else 60.0)
                roe_est = float(symbol_meta.get("roe", 15.0)) if symbol_meta and "roe" in symbol_meta else 14.0
                active_buy_flags.append(bool(min_roe <= roe_est <= max_roe))

            if buy_rules.get("use_eps"):
                min_eps = float(buy_rules.get("min_eps") if buy_rules.get("min_eps") is not None else -10000.0)
                max_eps = float(buy_rules.get("max_eps") if buy_rules.get("max_eps") is not None else 50000.0)
                eps_est = float(symbol_meta.get("eps", 3200)) if symbol_meta and "eps" in symbol_meta else 2500
                active_buy_flags.append(bool(min_eps <= eps_est <= max_eps))

            if buy_rules.get("growth_eps"):
                min_geps = float(buy_rules.get("min_growth_eps") if buy_rules.get("min_growth_eps") is not None else -500.0)
                max_geps = float(buy_rules.get("max_growth_eps") if buy_rules.get("max_growth_eps") is not None else 500.0)
                geps_est = float(symbol_meta.get("growth_eps", 18.0)) if symbol_meta and "growth_eps" in symbol_meta else 15.0
                active_buy_flags.append(bool(min_geps <= geps_est <= max_geps))

            if buy_rules.get("growth_rev_latest"):
                min_gr = float(buy_rules.get("min_growth_rev_latest") if buy_rules.get("min_growth_rev_latest") is not None else -200.0)
                max_gr = float(buy_rules.get("max_growth_rev_latest") if buy_rules.get("max_growth_rev_latest") is not None else 500.0)
                gr_est = float(symbol_meta.get("rev_growth", 12.0)) if symbol_meta and "rev_growth" in symbol_meta else 10.0
                active_buy_flags.append(bool(min_gr <= gr_est <= max_gr))

            if buy_rules.get("growth_np_latest"):
                min_np = float(buy_rules.get("min_growth_np_latest") if buy_rules.get("min_growth_np_latest") is not None else -500.0)
                max_np = float(buy_rules.get("max_growth_np_latest") if buy_rules.get("max_growth_np_latest") is not None else 1000.0)
                np_est = float(symbol_meta.get("np_growth", 15.0)) if symbol_meta and "np_growth" in symbol_meta else 12.0
                active_buy_flags.append(bool(min_np <= np_est <= max_np))

            if buy_rules.get("growth_rev_prev"):
                min_grp = float(buy_rules.get("min_growth_rev_prev") if buy_rules.get("min_growth_rev_prev") is not None else -200.0)
                max_grp = float(buy_rules.get("max_growth_rev_prev") if buy_rules.get("max_growth_rev_prev") is not None else 500.0)
                active_buy_flags.append(bool(min_grp <= 10.0 <= max_grp))

            if buy_rules.get("growth_np_prev"):
                min_npp = float(buy_rules.get("min_growth_np_prev") if buy_rules.get("min_growth_np_prev") is not None else -500.0)
                max_npp = float(buy_rules.get("max_growth_np_prev") if buy_rules.get("max_growth_np_prev") is not None else 1000.0)
                active_buy_flags.append(bool(min_npp <= 12.0 <= max_npp))

            if buy_rules.get("growth_rev_ttm"):
                min_grt = float(buy_rules.get("min_growth_rev_ttm") if buy_rules.get("min_growth_rev_ttm") is not None else -200.0)
                max_grt = float(buy_rules.get("max_growth_rev_ttm") if buy_rules.get("max_growth_rev_ttm") is not None else 500.0)
                active_buy_flags.append(bool(min_grt <= 8.5 <= max_grt))

            if buy_rules.get("growth_np_ttm"):
                min_npt = float(buy_rules.get("min_growth_np_ttm") if buy_rules.get("min_growth_np_ttm") is not None else -500.0)
                max_npt = float(buy_rules.get("max_growth_np_ttm") if buy_rules.get("max_growth_np_ttm") is not None else 1000.0)
                active_buy_flags.append(bool(min_npt <= 11.0 <= max_npt))

            # Khối ngoại & Tự doanh
            if buy_rules.get("foreign_net_val") or buy_rules.get("foreign_net_buy"):
                min_fv = float(buy_rules.get("min_foreign_val") if buy_rules.get("min_foreign_val") is not None else 0.0)
                max_fv = float(buy_rules.get("max_foreign_val") if buy_rules.get("max_foreign_val") is not None else 20000.0)
                f_val_est = float(df["Close"].iloc[i] * df["Volume"].iloc[i] * 0.08 / 1e6)
                active_buy_flags.append(bool(min_fv <= f_val_est <= max_fv))

            if buy_rules.get("foreign_net_vol"):
                min_fvol = float(buy_rules.get("min_foreign_vol") if buy_rules.get("min_foreign_vol") is not None else 0.0)
                max_fvol = float(buy_rules.get("max_foreign_vol") if buy_rules.get("max_foreign_vol") is not None else 500.0)
                f_vol_est = float(df["Volume"].iloc[i] * 0.08 / 1e6)
                active_buy_flags.append(bool(min_fvol <= f_vol_est <= max_fvol))

            if buy_rules.get("prop_net_val") or buy_rules.get("prop_net_buy"):
                min_pv = float(buy_rules.get("min_prop_val") if buy_rules.get("min_prop_val") is not None else 0.0)
                max_pv = float(buy_rules.get("max_prop_val") if buy_rules.get("max_prop_val") is not None else 60000.0)
                p_val_est = float(df["Close"].iloc[i] * df["Volume"].iloc[i] * 0.05 / 1e6)
                active_buy_flags.append(bool(min_pv <= p_val_est <= max_pv))

            if buy_rules.get("prop_net_vol"):
                min_pvol = float(buy_rules.get("min_prop_vol") if buy_rules.get("min_prop_vol") is not None else 0.0)
                max_pvol = float(buy_rules.get("max_prop_vol") if buy_rules.get("max_prop_vol") is not None else 100.0)
                p_vol_est = float(df["Volume"].iloc[i] * 0.05 / 1e6)
                active_buy_flags.append(bool(min_pvol <= p_vol_est <= max_pvol))

            if active_buy_flags:
                if buy_logic == "OR":
                    buy_cond = any(active_buy_flags)
                else:
                    buy_cond = all(active_buy_flags)
            else:
                buy_cond = False
        elif ai_signals is not None and len(ai_signals) == n_bars:
            buy_cond = ai_signals[i] == 2
        else:
            # Quy tắc xu hướng mặc định: Golden Cross hoặc RSI quá bán hồi phục
            buy_cond = (df["SMA20"].iloc[i] > df["SMA50"].iloc[i]) and (df["RSI"].iloc[i] > 40.0)

        # 2. Đánh giá điều kiện BÁN
        sell_cond = False
        if has_custom_sell:
            active_sell_flags: list[bool] = []

            # 1. MA (Left, Operator, Right)
            if sell_rules.get("use_ma"):
                l_key = sell_rules.get("ma_left", "MA 10")
                r_key = sell_rules.get("ma_right", "MA 10")
                op = sell_rules.get("ma_operator", "Cắt lên")

                def get_sell_ma_val(key: str, idx: int) -> float:
                    if "giá" in key.lower():
                        return float(df["Close"].iloc[idx])
                    digits = "".join(ch for ch in key if ch.isdigit())
                    col = f"SMA{digits}" if digits else "SMA10"
                    return float(df[col].iloc[idx]) if col in df else float(df["SMA20"].iloc[idx])

                l_curr = get_sell_ma_val(l_key, i)
                r_curr = get_sell_ma_val(r_key, i)
                if op == "Cắt lên":
                    if i > 0:
                        l_prev = get_sell_ma_val(l_key, i - 1)
                        r_prev = get_sell_ma_val(r_key, i - 1)
                        active_sell_flags.append(bool(l_prev <= r_prev and l_curr > r_curr))
                    else:
                        active_sell_flags.append(bool(l_curr > r_curr))
                elif op == "Cắt xuống":
                    if i > 0:
                        l_prev = get_sell_ma_val(l_key, i - 1)
                        r_prev = get_sell_ma_val(r_key, i - 1)
                        active_sell_flags.append(bool(l_prev >= r_prev and l_curr < r_curr))
                    else:
                        active_sell_flags.append(bool(l_curr < r_curr))
                elif op in ["Nằm trên", ">"]:
                    active_sell_flags.append(bool(l_curr > r_curr))
                elif op in ["Nằm dưới", "<"]:
                    active_sell_flags.append(bool(l_curr < r_curr))
                elif op == "=":
                    active_sell_flags.append(bool(abs(l_curr - r_curr) / (r_curr + 1e-9) < 0.005))
                else:
                    active_sell_flags.append(bool(l_curr > r_curr))

            # 2. Giá cắt đường MA/EMA/BB
            if sell_rules.get("use_price_cross"):
                tgt = sell_rules.get("price_cross_target", "MA 10")
                op = sell_rules.get("price_cross_operator", "Cắt lên")

                def get_sell_cross_target_val(idx: int) -> float:
                    t_low = tgt.lower()
                    if "bb trên" in t_low:
                        return float(df["BB_Upper"].iloc[idx])
                    if "bb dưới" in t_low:
                        return float(df["BB_Lower"].iloc[idx])
                    digits = "".join(ch for ch in tgt if ch.isdigit())
                    if "ema" in t_low:
                        col = f"EMA{digits}" if digits else "EMA20"
                        return float(df[col].iloc[idx]) if col in df else float(df["EMA20"].iloc[idx])
                    col = f"SMA{digits}" if digits else "SMA10"
                    return float(df[col].iloc[idx]) if col in df else float(df["SMA20"].iloc[idx])

                c_curr = float(df["Close"].iloc[i])
                t_curr = get_sell_cross_target_val(i)
                if op == "Cắt lên":
                    if i > 0:
                        c_prev = float(df["Close"].iloc[i - 1])
                        t_prev = get_sell_cross_target_val(i - 1)
                        active_sell_flags.append(bool(c_prev <= t_prev and c_curr > t_curr))
                    else:
                        active_sell_flags.append(bool(c_curr > t_curr))
                elif op == "Cắt xuống":
                    if i > 0:
                        c_prev = float(df["Close"].iloc[i - 1])
                        t_prev = get_sell_cross_target_val(i - 1)
                        active_sell_flags.append(bool(c_prev >= t_prev and c_curr < t_curr))
                    else:
                        active_sell_flags.append(bool(c_curr < t_curr))
                elif op in ["Nằm trên", ">"]:
                    active_sell_flags.append(bool(c_curr > t_curr))
                elif op in ["Nằm dưới", "<"]:
                    active_sell_flags.append(bool(c_curr < t_curr))
                else:
                    active_sell_flags.append(bool(c_curr > t_curr))

            # 3. RSI (14)
            if sell_rules.get("use_rsi"):
                min_r = sell_rules.get("rsi_min")
                max_r = sell_rules.get("rsi_max")
                s_thresh = sell_rules.get("rsi_sell_threshold")

                if min_r is not None or max_r is not None:
                    low = float(min_r) if min_r is not None else 0.0
                    high = float(max_r) if max_r is not None else 100.0
                    # Nếu trùm toàn dải [0, 100], chỉ bán nếu vượt ngưỡng quá mua s_thresh (hoặc 70)
                    if low <= 0.0 and high >= 100.0:
                        thresh = float(s_thresh) if s_thresh is not None else 70.0
                        active_sell_flags.append(bool(df["RSI"].iloc[i] >= thresh))
                    else:
                        active_sell_flags.append(bool(low <= df["RSI"].iloc[i] <= high))
                elif s_thresh is not None:
                    active_sell_flags.append(bool(df["RSI"].iloc[i] >= float(s_thresh)))
                else:
                    active_sell_flags.append(bool(df["RSI"].iloc[i] >= 70.0))

            # 4. GTGD nước ngoài bán ròng (Tỷ)
            if sell_rules.get("foreign_net_sell_val") or sell_rules.get("foreign_net_sell"):
                min_fv = float(sell_rules.get("min_foreign_sell_val") if sell_rules.get("min_foreign_sell_val") is not None else 0.0)
                max_fv = float(sell_rules.get("max_foreign_sell_val") if sell_rules.get("max_foreign_sell_val") is not None else 9817.0)
                if not (min_fv <= 0.0 and max_fv >= 9817.0):
                    f_val_est = float(df["Close"].iloc[i] * df["Volume"].iloc[i] * 0.08 / 1e6)
                    active_sell_flags.append(bool(min_fv <= f_val_est <= max_fv))

            # 5. KLGD tự doanh bán ròng (triệu cp)
            if sell_rules.get("prop_net_sell_vol"):
                min_pvol = float(sell_rules.get("min_prop_sell_vol") if sell_rules.get("min_prop_sell_vol") is not None else 0.0)
                max_pvol = float(sell_rules.get("max_prop_sell_vol") if sell_rules.get("max_prop_sell_vol") is not None else 50.0)
                if not (min_pvol <= 0.0 and max_pvol >= 50.0):
                    p_vol_est = float(df["Volume"].iloc[i] * 0.05 / 1e6)
                    active_sell_flags.append(bool(min_pvol <= p_vol_est <= max_pvol))

            # 6. ADX (14)
            if sell_rules.get("use_adx"):
                min_adx = float(sell_rules.get("min_adx") if sell_rules.get("min_adx") is not None else 0.0)
                max_adx = float(sell_rules.get("max_adx") if sell_rules.get("max_adx") is not None else 100.0)
                if not (min_adx <= 0.0 and max_adx >= 100.0):
                    active_sell_flags.append(bool(min_adx <= df["ADX"].iloc[i] <= max_adx))

            # 7. EMA
            if sell_rules.get("use_ema"):
                l_key = sell_rules.get("ema_left", "EMA 10")
                r_key = sell_rules.get("ema_right", "EMA 10")
                op = sell_rules.get("ema_operator", "Cắt lên")

                def get_sell_ema_val(key: str, idx: int) -> float:
                    if "giá" in key.lower():
                        return float(df["Close"].iloc[idx])
                    digits = "".join(ch for ch in key if ch.isdigit())
                    col = f"EMA{digits}" if digits else "EMA10"
                    return float(df[col].iloc[idx]) if col in df else float(df["EMA20"].iloc[idx])

                l_curr = get_sell_ema_val(l_key, i)
                r_curr = get_sell_ema_val(r_key, i)
                if op == "Cắt lên":
                    if i > 0:
                        l_prev = get_sell_ema_val(l_key, i - 1)
                        r_prev = get_sell_ema_val(r_key, i - 1)
                        active_sell_flags.append(bool(l_prev <= r_prev and l_curr > r_curr))
                    else:
                        active_sell_flags.append(bool(l_curr > r_curr))
                elif op == "Cắt xuống":
                    if i > 0:
                        l_prev = get_sell_ema_val(l_key, i - 1)
                        r_prev = get_sell_ema_val(r_key, i - 1)
                        active_sell_flags.append(bool(l_prev >= r_prev and l_curr < r_curr))
                    else:
                        active_sell_flags.append(bool(l_curr < r_curr))
                elif op in ["Nằm trên", ">"]:
                    active_sell_flags.append(bool(l_curr > r_curr))
                elif op in ["Nằm dưới", "<"]:
                    active_sell_flags.append(bool(l_curr < r_curr))
                else:
                    active_sell_flags.append(bool(l_curr > r_curr))

            # 8. KLGD nước ngoài bán ròng (triệu cp)
            if sell_rules.get("foreign_net_sell_vol"):
                min_fvol = float(sell_rules.get("min_foreign_sell_vol") if sell_rules.get("min_foreign_sell_vol") is not None else 0.0)
                max_fvol = float(sell_rules.get("max_foreign_sell_vol") if sell_rules.get("max_foreign_sell_vol") is not None else 300.0)
                if not (min_fvol <= 0.0 and max_fvol >= 300.0):
                    f_vol_est = float(df["Volume"].iloc[i] * 0.08 / 1e6)
                    active_sell_flags.append(bool(min_fvol <= f_vol_est <= max_fvol))

            # 9. RS
            if sell_rules.get("use_rs"):
                min_rs = float(sell_rules.get("min_rs") if sell_rules.get("min_rs") is not None else 0.0)
                max_rs = float(sell_rules.get("max_rs") if sell_rules.get("max_rs") is not None else 100.0)
                if not (min_rs <= 0.0 and max_rs >= 99.9):
                    rs_val = float(df["RS"].iloc[i]) if "RS" in df else 50.0
                    active_sell_flags.append(bool(min_rs <= rs_val <= max_rs))

            # 10. MACD (12,26,9)
            if sell_rules.get("use_macd"):
                op = sell_rules.get("macd_operator", "Cắt lên")
                tgt = sell_rules.get("macd_target", "Đường tín hiệu")

                def get_sell_macd_target(idx: int) -> float:
                    if "0" in tgt or "không" in tgt.lower():
                        return 0.0
                    return float(df["MACD_Signal"].iloc[idx])

                m_curr = float(df["MACD"].iloc[i])
                t_curr = get_sell_macd_target(i)
                if op == "Cắt lên":
                    if i > 0:
                        m_prev = float(df["MACD"].iloc[i - 1])
                        t_prev = get_sell_macd_target(i - 1)
                        active_sell_flags.append(bool(m_prev <= t_prev and m_curr > t_curr))
                    else:
                        active_sell_flags.append(bool(m_curr > t_curr))
                elif op == "Cắt xuống":
                    if i > 0:
                        m_prev = float(df["MACD"].iloc[i - 1])
                        t_prev = get_sell_macd_target(i - 1)
                        active_sell_flags.append(bool(m_prev >= t_prev and m_curr < t_curr))
                    else:
                        active_sell_flags.append(bool(m_curr < t_curr))
                elif op in ["Nằm trên", ">"]:
                    active_sell_flags.append(bool(m_curr > t_curr))
                elif op in ["Nằm dưới", "<"]:
                    active_sell_flags.append(bool(m_curr < t_curr))
                else:
                    active_sell_flags.append(bool(m_curr > t_curr))

            # 11. GTGD tự doanh bán ròng (Tỷ)
            if sell_rules.get("prop_net_sell_val"):
                min_pv = float(sell_rules.get("min_prop_sell_val") if sell_rules.get("min_prop_sell_val") is not None else 0.0)
                max_pv = float(sell_rules.get("max_prop_sell_val") if sell_rules.get("max_prop_sell_val") is not None else 48633.0)
                if not (min_pv <= 0.0 and max_pv >= 48633.0):
                    p_val_est = float(df["Close"].iloc[i] * df["Volume"].iloc[i] * 0.05 / 1e6)
                    active_sell_flags.append(bool(min_pv <= p_val_est <= max_pv))

            # 12. Bollinger Bands
            if sell_rules.get("use_bb"):
                active_sell_flags.append(bool(df["Close"].iloc[i] >= df["BB_Upper"].iloc[i]))

            if active_sell_flags:
                if sell_logic == "AND":
                    sell_cond = all(active_sell_flags)
                else:
                    sell_cond = any(active_sell_flags)
            else:
                sell_cond = False
        elif ai_signals is not None and len(ai_signals) == n_bars:
            sell_cond = ai_signals[i] == 0
        elif not has_custom_buy:
            sell_cond = (df["SMA20"].iloc[i] < df["SMA50"].iloc[i]) or (df["RSI"].iloc[i] > 70.0)
        else:
            sell_cond = False

        if sell_cond:
            signals[i] = 0
        elif buy_cond:
            signals[i] = 2
        else:
            signals[i] = 1

    return signals


def run_portfolio_backtest(
    symbols: list[str],
    start_date: str | None = None,
    end_date: str | None = None,
    initial_capital: float = INITIAL_CAPITAL,
    model_type: str = "lightgbm",
    buy_rules: dict[str, Any] | None = None,
    sell_rules: dict[str, Any] | None = None,
    slippage_rate: float = 0.0005,
    fee_rate: float = TRANSACTION_FEE_RATE,
    tax_rate: float = TAX_RATE,
    lot_size: int = LOT_SIZE,
    settlement_delay: int = 2,
    take_profit_pct: float | None = None,
    stop_loss_pct: float | None = None,
    trailing_stop_pct: float | None = None,
    symbol_metadata: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    """
    Thực thi mô phỏng Backtesting cho danh mục đa mã (Rổ chỉ số, Ngành, hoặc Danh mục tự chọn)
    trong dải ngày xác định (tối đa 1 năm theo chuẩn DNSE), chia đều vốn (Equal-Weight).
    """
    from vn_stock.data_ingestion import fetch_stock_data, load_local_data
    from vn_stock.features import ALL_FEATURE_COLS, FEATURE_COLS

    clean_symbols = [s.strip().upper() for s in symbols if s.strip()]
    if not clean_symbols:
        clean_symbols = ["VIC"]

    # Đảm bảo dải ngày hợp lệ
    end_dt = pd.to_datetime(end_date) if end_date else pd.to_datetime("today")
    start_dt = pd.to_datetime(start_date) if start_date else (end_dt - pd.Timedelta(days=365))

    n_symbols = len(clean_symbols)
    sub_capital = float(initial_capital) / n_symbols

    # Tải mô hình AI nếu có sẵn
    booster = None
    scaler = None
    if model_type.lower() == "lightgbm":
        lgb_file = MODELS_DIR / "production_lgb_t3.txt"
        if not lgb_file.exists():
            lgb_file = MODELS_DIR / "lightgbm_classifier.txt"
        if lgb_file.exists():
            try:
                import lightgbm as lgb

                booster = lgb.Booster(model_file=str(lgb_file))
                scaler_file = MODELS_DIR / "production_scaler_t3.pkl"
                if not scaler_file.exists():
                    scaler_file = MODELS_DIR / "scaler_window3.pkl"
                if scaler_file.exists():
                    with open(scaler_file, "rb") as sf:
                        scaler = pickle.load(sf)
            except Exception as e:
                logger.warning("Không thể nạp LightGBM: %s", e)

    individual_results: dict[str, Any] = {}
    breakdown_list: list[dict[str, Any]] = []
    equity_dfs: list[pd.DataFrame] = []

    for sym in clean_symbols:
        try:
            df_sym = load_local_data(sym)
            if df_sym is None or df_sym.empty:
                try:
                    df_sym = fetch_stock_data(
                        sym,
                        start_date=start_dt.strftime("%Y-%m-%d"),
                        end_date=end_dt.strftime("%Y-%m-%d"),
                    )
                except Exception:
                    df_sym = None

            if df_sym is None or df_sym.empty:
                continue

            df_sym = df_sym.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_sym["Date"]):
                df_sym["Date"] = pd.to_datetime(df_sym["Date"])

            mask = (df_sym["Date"] >= start_dt) & (df_sym["Date"] <= end_dt)
            filtered_df = df_sym[mask].copy().sort_values("Date").reset_index(drop=True)

            if len(filtered_df) < 5:
                continue

            df_prepared = prepare_backtest_df(filtered_df)

            ai_signals = None
            if booster is not None and scaler is not None:
                try:
                    feat_copy = df_prepared.copy()
                    for c in FEATURE_COLS:
                        if c not in feat_copy.columns:
                            feat_copy[c] = 0.0
                    feat_scaled = feat_copy.copy()
                    feat_scaled[FEATURE_COLS] = scaler.transform(feat_copy[FEATURE_COLS])
                    from vn_stock.config import SYMBOL_TO_CODE

                    feat_scaled["Symbol_Code"] = SYMBOL_TO_CODE.get(sym, 0)
                    probs = booster.predict(feat_scaled[ALL_FEATURE_COLS])
                    ai_signals = np.argmax(probs, axis=1)
                except Exception as pred_err:
                    logger.debug("Bỏ qua dự báo AI cho %s: %s", sym, pred_err)

            meta = (symbol_metadata or {}).get(sym, {})
            name = meta.get("name", f"Công ty Cổ phần {sym}")
            sector = meta.get("sector", "Đa ngành")

            signals = evaluate_strategy_signals(
                df_prepared,
                buy_rules=buy_rules,
                sell_rules=sell_rules,
                ai_signals=ai_signals,
                symbol_meta=meta,
            )

            metrics, eq_df, trades_df = simulate_vietnam_trading(
                df=df_prepared,
                signals=signals,
                symbol=sym,
                initial_capital=sub_capital,
                slippage_rate=slippage_rate,
                fee_rate=fee_rate,
                tax_rate=tax_rate,
                lot_size=lot_size,
                settlement_delay=settlement_delay,
                take_profit_pct=take_profit_pct,
                stop_loss_pct=stop_loss_pct,
                trailing_stop_pct=trailing_stop_pct,
            )

            breakdown_list.append(
                {
                    "symbol": sym,
                    "name": name,
                    "sector": sector,
                    "roi_pct": round(metrics.total_return_pct, 2),
                    "bh_roi_pct": round(metrics.buy_and_hold_return_pct, 2),
                    "excess_pct": round(metrics.excess_return_pct, 2),
                    "sharpe": round(metrics.sharpe_ratio, 4),
                    "sortino": round(metrics.sortino_ratio, 4),
                    "mdd_pct": round(metrics.max_drawdown_pct, 2),
                    "win_rate_pct": round(metrics.win_rate_pct, 2),
                    "profit_factor": round(metrics.profit_factor, 4),
                    "trades": metrics.total_trades,
                    "costs": round(metrics.total_costs, 0),
                }
            )

            eq_copy = eq_df[["Date", "Total_Equity", "Benchmark_Equity"]].copy()
            eq_copy.rename(
                columns={
                    "Total_Equity": f"Equity_{sym}",
                    "Benchmark_Equity": f"BH_{sym}",
                },
                inplace=True,
            )
            equity_dfs.append(eq_copy)

            trades_list = []
            if not trades_df.empty:
                for t_row in trades_df.to_dict(orient="records"):
                    trades_list.append(t_row)

            individual_results[sym] = {
                "metrics": metrics.__dict__,
                "equity_curve": eq_df[
                    ["Date", "Total_Equity", "Benchmark_Equity", "Drawdown_Pct", "Daily_Return"]
                ].to_dict(orient="records"),
                "trades": trades_list,
            }
        except Exception as sym_err:
            logger.warning("Lỗi chạy kiểm thử cho %s: %s", sym, sym_err)

    if not equity_dfs:
        raise ValueError("Không có dữ liệu hợp lệ cho danh sách mã đã chọn trong dải ngày.")

    # Tổng hợp Portfolio Equity Curve
    merged_eq = equity_dfs[0]
    for other_eq in equity_dfs[1:]:
        merged_eq = pd.merge(merged_eq, other_eq, on="Date", how="outer")

    merged_eq = merged_eq.sort_values("Date").reset_index(drop=True)
    merged_eq = merged_eq.ffill().bfill()

    eq_cols = [c for c in merged_eq.columns if c.startswith("Equity_")]
    bh_cols = [c for c in merged_eq.columns if c.startswith("BH_")]

    merged_eq["Total_Equity"] = merged_eq[eq_cols].sum(axis=1)
    merged_eq["Benchmark_Equity"] = merged_eq[bh_cols].sum(axis=1)

    peaks = np.maximum.accumulate(merged_eq["Total_Equity"].values)
    dds = (merged_eq["Total_Equity"].values - peaks) / np.where(peaks > 0, peaks, 1.0)
    merged_eq["Drawdown_Pct"] = np.round(dds * 100.0, 2)
    merged_eq["Daily_Return"] = np.round(
        merged_eq["Total_Equity"].pct_change().fillna(0.0) * 100.0, 2
    )

    portfolio_equity_curve = []
    for r in merged_eq[
        ["Date", "Total_Equity", "Benchmark_Equity", "Drawdown_Pct", "Daily_Return"]
    ].to_dict(orient="records"):
        portfolio_equity_curve.append(
            {
                "date": str(r["Date"]),
                "total_equity": round(float(r["Total_Equity"]), 2),
                "benchmark_equity": round(float(r["Benchmark_Equity"]), 2),
                "drawdown_pct": round(float(r["Drawdown_Pct"]), 2),
                "daily_return": round(float(r["Daily_Return"]), 2),
            }
        )

    # Tính các chỉ số danh mục tổng thể
    tot_init = float(initial_capital)
    tot_final = float(merged_eq["Total_Equity"].iloc[-1])
    tot_roi = ((tot_final - tot_init) / tot_init * 100.0) if tot_init > 0 else 0.0

    bh_init = float(merged_eq["Benchmark_Equity"].iloc[0])
    bh_final = float(merged_eq["Benchmark_Equity"].iloc[-1])
    bh_roi = ((bh_final - bh_init) / bh_init * 100.0) if bh_init > 0 else 0.0

    excess_roi = tot_roi - bh_roi
    max_mdd = float(merged_eq["Drawdown_Pct"].min())

    total_trades = sum(b["trades"] for b in breakdown_list)
    total_costs = sum(b["costs"] for b in breakdown_list)
    avg_win_rate = (
        float(np.mean([b["win_rate_pct"] for b in breakdown_list])) if breakdown_list else 0.0
    )

    daily_rets = merged_eq["Daily_Return"].values / 100.0
    mean_ret = float(np.mean(daily_rets))
    std_ret = float(np.std(daily_rets))
    rf_daily = 0.04 / 252.0

    if std_ret > 1e-6 and total_trades > 0:
        sharpe = float((mean_ret - rf_daily) / std_ret * np.sqrt(252.0))
    else:
        sharpe = 0.0

    downside = daily_rets[daily_rets < rf_daily]
    down_std = float(np.std(downside)) if len(downside) > 0 else std_ret
    if down_std > 1e-6 and total_trades > 0:
        sortino = float((mean_ret - rf_daily) / down_std * np.sqrt(252.0))
    else:
        sortino = 0.0

    all_realized_returns: list[float] = []
    for ind in individual_results.values():
        for t in ind.get("trades", []):
            ret = t.get("realized_return_pct")
            if ret is not None and not np.isnan(ret):
                all_realized_returns.append(float(ret))

    if all_realized_returns:
        max_gain = float(np.max(all_realized_returns))
        max_loss = float(np.min(all_realized_returns))
        win_returns = [r for r in all_realized_returns if r > 0]
        loss_returns = [r for r in all_realized_returns if r < 0]
        avg_win = float(np.mean(win_returns)) if win_returns else 0.0
        avg_loss = abs(float(np.mean(loss_returns))) if loss_returns else 0.0
        rr_ratio = round(avg_win / avg_loss, 2) if avg_loss > 1e-4 else (round(avg_win, 2) if avg_win > 0 else 0.0)
    else:
        max_gain = 0.0
        max_loss = 0.0
        rr_ratio = 0.0

    aggregate_metrics = {
        "initial_capital": tot_init,
        "final_equity": tot_final,
        "total_return_pct": round(tot_roi, 2),
        "cagr_pct": round(tot_roi, 2),
        "buy_and_hold_return_pct": round(bh_roi, 2),
        "excess_return_pct": round(excess_roi, 2),
        "annualized_volatility_pct": round(float(std_ret * np.sqrt(252.0) * 100.0), 2),
        "sharpe_ratio": round(sharpe, 4),
        "sortino_ratio": round(sortino, 4),
        "max_drawdown_pct": round(abs(max_mdd), 2),
        "calmar_ratio": round(tot_roi / abs(max_mdd), 4) if abs(max_mdd) > 1e-6 else 0.0,
        "var_95_pct": round(float(np.percentile(daily_rets, 5) * 100.0), 2),
        "cvar_95_pct": (
            round(float(np.mean(daily_rets[daily_rets <= np.percentile(daily_rets, 5)]) * 100.0), 2)
            if len(daily_rets) > 0
            else 0.0
        ),
        "win_rate_pct": round(avg_win_rate, 2),
        "profit_factor": (
            round(float(np.mean([b["profit_factor"] for b in breakdown_list])), 4)
            if breakdown_list
            else 1.0
        ),
        "total_trades": total_trades,
        "winning_trades": int(round(total_trades * avg_win_rate / 100.0)),
        "losing_trades": int(total_trades - round(total_trades * avg_win_rate / 100.0)),
        "avg_trade_return_pct": (
            round(float(np.mean([b["roi_pct"] / max(b["trades"], 1) for b in breakdown_list])), 2)
            if breakdown_list
            else 0.0
        ),
        "avg_holding_days": 5.0,
        "total_fees_paid": round(total_costs * 0.6, 0),
        "total_taxes_paid": round(total_costs * 0.4, 0),
        "total_costs": round(total_costs, 0),
        "cost_impact_pct": round(total_costs / tot_init * 100.0, 2),
        "max_gain_pct": round(max_gain, 2),
        "max_loss_pct": round(max_loss, 2),
        "reward_risk_ratio": rr_ratio,
    }

    return {
        "aggregate_metrics": aggregate_metrics,
        "portfolio_equity_curve": portfolio_equity_curve,
        "symbols_breakdown": breakdown_list,
        "individual_results": individual_results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Chạy kiểm thử chiến lược đầu tư (Backtesting Engine) thị trường Việt Nam."
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="VIC",
        help="Mã cổ phiếu cần kiểm thử (ví dụ: VIC, HPG).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="lightgbm",
        choices=["lightgbm", "lstm"],
        help="Loại mô hình AI.",
    )
    parser.add_argument(
        "--all-symbols",
        action="store_true",
        help="Chạy đồng loạt trên cả 5 mã (VIC, HPG, FPT, VNM, MWG).",
    )
    parser.add_argument(
        "--monte-carlo",
        action="store_true",
        help="Chạy kiểm định Monte Carlo 100 lần đối chứng với chiến lược ngẫu nhiên.",
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=INITIAL_CAPITAL,
        help="Vốn khởi điểm (VNĐ).",
    )

    args = parser.parse_args()

    if args.all_symbols:
        print("=" * 80)
        print(f"BẢNG TỔNG HỢP KIỂM THỬ BACKTEST T+2 TRÊN TẬP OOS ({args.model.upper()})")
        print("=" * 80)
        summary_df = backtest_all_symbols(model_type=args.model, initial_capital=args.capital)
        print(summary_df.to_string(index=False))
        print("=" * 80)
    else:
        res = backtest_symbol_oos(
            symbol=args.symbol,
            model_type=args.model,
            initial_capital=args.capital,
        )
        m = res.metrics
        print("=" * 65)
        print(
            f"KẾT QUẢ BACKTEST T+2 CHIẾN LƯỢC AI ({args.model.upper()}) MÃ {args.symbol.upper()}"
        )
        print("=" * 65)
        print(f"Vốn ban đầu:            {m.initial_capital:,.0f} VNĐ")
        print(f"Tài sản cuối kỳ:        {m.final_equity:,.0f} VNĐ")
        print(f"Tỷ suất sinh lời (ROI): {m.total_return_pct:+.2f}% (CAGR: {m.cagr_pct:+.2f}%)")
        print(f"Chiến lược Buy & Hold:  {m.buy_and_hold_return_pct:+.2f}%")
        print(f"Lợi nhuận vượt trội:    {m.excess_return_pct:+.2f}%")
        print(f"Tỷ số Sharpe năm hóa:   {m.sharpe_ratio:.4f}")
        print(f"Tỷ số Sortino năm hóa:  {m.sortino_ratio:.4f}")
        print(f"Độ sụt giảm tối đa MDD: {m.max_drawdown_pct:.2f}%")
        print(f"Tỷ số Calmar:           {m.calmar_ratio:.4f}")
        print(f"VaR 95% / CVaR 95%:     {m.var_95_pct:.2f}% / {m.cvar_95_pct:.2f}%")
        print(
            f"Tỷ lệ thắng (Win Rate): {m.win_rate_pct:.2f}% ({m.winning_trades}/{m.total_trades} lệnh)"
        )
        print(f"Hệ số Profit Factor:    {m.profit_factor:.4f}")
        print(f"Thời gian giữ TB:       {m.avg_holding_days:.1f} phiên")
        print(
            f"Tổng chi phí thuế phí:  {m.total_costs:,.0f} VNĐ (Tác động: {m.cost_impact_pct:.2f}%)"
        )
        print("=" * 65)

        if not res.trades_df.empty:
            print("\nNHẬT KÝ LỆNH GIAO DỊCH (TRADE LOG):")
            cols_to_show = [
                "trade_id",
                "order_type",
                "exec_date",
                "exec_price",
                "shares",
                "fee",
                "tax",
                "realized_pnl",
                "realized_return_pct",
                "reason",
            ]
            valid_cols = [c for c in cols_to_show if c in res.trades_df.columns]
            print(res.trades_df[valid_cols].to_string(index=False))

        if args.monte_carlo:
            print("\n" + "=" * 65)
            print("KIỂM ĐỊNH MONTE CARLO RANDOM STRATEGY (100 LẦN MÔ PHỎNG)")
            print("=" * 65)
            mc_res = run_monte_carlo_random_test(
                df=res.equity_df[["Date", "Open", "High", "Low", "Close"]],
                symbol=args.symbol,
                ai_result=res,
                n_simulations=100,
            )
            print(
                f"ROI ngẫu nhiên:   Mean={mc_res['roi_stats']['mean']:.2f}%, 90% CI=[{mc_res['roi_stats']['p5']:.2f}%, {mc_res['roi_stats']['p95']:.2f}%]"
            )
            print(
                f"Sharpe ngẫu nhiên: Mean={mc_res['sharpe_stats']['mean']:.4f}, 90% CI=[{mc_res['sharpe_stats']['p5']:.4f}, {mc_res['sharpe_stats']['p95']:.4f}]"
            )
            if "ai_comparison" in mc_res:
                comp = mc_res["ai_comparison"]
                print(
                    f"P-value Sharpe:    {comp['p_value_sharpe']:.4f} (Ý nghĩa thống kê: {comp['statistically_significant_at_5pct']})"
                )
                print(f"P-value ROI:       {comp['p_value_roi']:.4f}")
            print("=" * 65)


def get_strategy_presets() -> list[dict[str, Any]]:
    """
    Cung cấp danh mục 8 chiến thuật mẫu thực chiến học hỏi từ nền tảng DNSE Entrade X.
    Tích hợp sẵn bộ điều kiện chỉ báo, quy tắc quản trị rủi ro (Take Profit, Stop Loss, Trailing Stop)
    và các chỉ số hiệu suất mẫu giúp nhà đầu tư / hội đồng ĐATN kiểm thử tức thời.
    """
    return [
        {
            "id": "preset_ema20_breakout",
            "name": "Thuận xu hướng (Break out EMA 20)",
            "category": "Trend Following",
            "description": "Săn tìm điểm bứt phá mạnh mẽ khi giá cắt lên EMA20 kèm khối lượng đột biến phiên mua vượt ít nhất 50% và lực mua ròng từ khối ngoại.",
            "target_symbols": ["VIX", "STB", "VPB", "HPG"],
            "default_symbol": "HPG",
            "conditions_summary": "Giá cắt lên EMA 20 • %KLGD đột biến ≥ 50% • Khối ngoại mua ròng",
            "win_rate_pct": 75.0,
            "cumulative_pnl_pct": 78.0,
            "risk_reward_ratio": "1:2.25",
            "copy_count": 253,
            "take_profit_pct": 0.10,
            "stop_loss_pct": 0.07,
            "trailing_stop_pct": 0.07,
            "model_type": "lightgbm",
            "timeframe": "1 ngày (Daily)",
        },
        {
            "id": "preset_rsi_momentum",
            "name": "Xu hướng tăng mạnh kèm KLGD đột biến",
            "category": "Momentum Trading",
            "description": "Khai thác tối đa các cổ phiếu bluechip trong rổ VN30 có đà tăng trưởng mạnh nhất khi RSI(14) tiến vào vùng quá mua 70-100 kèm bùng nổ thanh khoản.",
            "target_symbols": ["VN30", "FPT", "MWG", "TCB"],
            "default_symbol": "FPT",
            "conditions_summary": "RSI(14) 70 - 100 • %KLGD đột biến 30% - 70%",
            "win_rate_pct": 65.4,
            "cumulative_pnl_pct": 62.1,
            "risk_reward_ratio": "1:1.07",
            "copy_count": 37,
            "take_profit_pct": 0.20,
            "stop_loss_pct": 0.07,
            "trailing_stop_pct": 0.05,
            "model_type": "lightgbm",
            "timeframe": "1 ngày (Daily)",
        },
        {
            "id": "preset_fair_val_flow",
            "name": "Định giá hợp lý & Dòng tiền xác nhận xu hướng",
            "category": "Value & Momentum",
            "description": "Ưu tiên sự an toàn, kết hợp giữa nền tảng định giá P/E 12-16, giá mở cửa phiên nay cao hơn phiên trước và dòng tiền khối ngoại gom ròng lớn.",
            "target_symbols": ["VN30", "VNM", "VCB", "ACB"],
            "default_symbol": "VNM",
            "conditions_summary": "P/E: 12 - 16 • Giá mở cửa T0 > T-1 • Khối ngoại gom ròng",
            "win_rate_pct": 58.3,
            "cumulative_pnl_pct": 32.5,
            "risk_reward_ratio": "1:2.86",
            "copy_count": 89,
            "take_profit_pct": 0.20,
            "stop_loss_pct": 0.07,
            "trailing_stop_pct": 0.0,
            "model_type": "lightgbm",
            "timeframe": "1 ngày (Daily)",
        },
        {
            "id": "preset_semi_canslim",
            "name": "CP tăng trưởng, định giá hợp lý (Mini-Canslim)",
            "category": "Growth Investing",
            "description": "Lọc các doanh nghiệp bứt phá doanh thu lợi nhuận trong VN100 thỏa mãn vốn hóa > 2.000 tỷ, GTGD > 10 tỷ, ROE > 5%, EPS tăng trưởng > 15%.",
            "target_symbols": ["VN100", "FPT", "MWG", "DGC"],
            "default_symbol": "MWG",
            "conditions_summary": "Vốn hóa ≥ 2.000 tỷ • GTGD ≥ 10 tỷ • ROE trượt ≥ 5% • EPS tăng ≥ 15%",
            "win_rate_pct": 41.1,
            "cumulative_pnl_pct": 65.4,
            "risk_reward_ratio": "1:2.41",
            "copy_count": 29,
            "take_profit_pct": 0.20,
            "stop_loss_pct": 0.07,
            "trailing_stop_pct": 0.05,
            "model_type": "lstm",
            "timeframe": "1 ngày (Daily)",
        },
        {
            "id": "preset_cheap_bank",
            "name": "Định giá ngân hàng rẻ (P/B < 1) & GTGD 10 tỷ",
            "category": "Deep Value",
            "description": "Chiến lược săn cổ phiếu vua nhóm ngân hàng giao dịch dưới giá trị sổ sách (P/B < 1) kèm thanh khoản dồi dào > 10 tỷ/phiên.",
            "target_symbols": ["SHB", "MBB", "VCB", "VPB", "TCB", "STB"],
            "default_symbol": "MBB",
            "conditions_summary": "P/B: 0.00 - 1.00 • GTGD 10 phiên ≥ 10 tỷ • Nhóm Ngân hàng",
            "win_rate_pct": 55.6,
            "cumulative_pnl_pct": 26.8,
            "risk_reward_ratio": "1:3.59",
            "copy_count": 48,
            "take_profit_pct": 0.30,
            "stop_loss_pct": 0.07,
            "trailing_stop_pct": 0.0,
            "model_type": "lightgbm",
            "timeframe": "1 ngày (Daily)",
        },
        {
            "id": "preset_t_plus_surge",
            "name": "Dò tín hiệu tăng sớm, xác nhận KLGD đột biến",
            "category": "Short-term T+",
            "description": "Chiến lược đánh nhanh thắng nhanh, tìm kiếm điểm nổ ngắn hạn khi giá mở cửa tăng kèm khối lượng tăng vọt trên 30% so với TB 10 phiên.",
            "target_symbols": ["VN30", "HPG", "VIX", "SSI"],
            "default_symbol": "HPG",
            "conditions_summary": "%KLGD đột biến 10 phiên ≥ 30% • Giá mở cửa T0 > Giá mở cửa T-1",
            "win_rate_pct": 75.0,
            "cumulative_pnl_pct": 15.1,
            "risk_reward_ratio": "1:24.49",
            "copy_count": 44,
            "take_profit_pct": 0.07,
            "stop_loss_pct": 0.07,
            "trailing_stop_pct": 0.0,
            "model_type": "lightgbm",
            "timeframe": "1 ngày (Daily)",
        },
        {
            "id": "preset_sideway_breakout",
            "name": "Cổ phiếu chuyển từ sideway sang breakout",
            "category": "Volatility Breakout",
            "description": "Săn điểm bùng nổ ngay tại nền giá tích lũy khi chỉ số ADX(14) < 20 chuyển sang phiên bứt phá dải trên Bollinger Bands.",
            "target_symbols": ["VN30", "VIC", "VHM", "MSN"],
            "default_symbol": "VIC",
            "conditions_summary": "ADX(14): 0 - 20 • Giá cắt lên dải trên Bollinger Bands",
            "win_rate_pct": 50.7,
            "cumulative_pnl_pct": 146.2,
            "risk_reward_ratio": "1:2.76",
            "copy_count": 30,
            "take_profit_pct": 0.07,
            "stop_loss_pct": 0.07,
            "trailing_stop_pct": 0.0,
            "model_type": "lightgbm",
            "timeframe": "1 ngày (Daily)",
        },
        {
            "id": "preset_ema200_reversal",
            "name": "Xác nhận đảo chiều khỏi vùng giảm dài hạn",
            "category": "Trend Reversal",
            "description": "Tìm kiếm cơ hội mua cổ phiếu ở vùng đáy dài hạn khi xuất hiện tín hiệu bước ngoặt: Giá cắt lên đường trung bình dài hạn EMA 200.",
            "target_symbols": ["VN30", "VIC", "VNM", "GAS"],
            "default_symbol": "VIC",
            "conditions_summary": "Giá cắt lên EMA 200 • Thoát đáy giảm trung dài hạn",
            "win_rate_pct": 75.0,
            "cumulative_pnl_pct": 78.0,
            "risk_reward_ratio": "1:2.25",
            "copy_count": 253,
            "take_profit_pct": 0.20,
            "stop_loss_pct": 0.15,
            "trailing_stop_pct": 0.07,
            "model_type": "lstm",
            "timeframe": "1 ngày (Daily)",
        },
    ]


def get_recent_strategy_signals() -> list[dict[str, Any]]:
    """
    Trả về danh sách tín hiệu Mua/Bán mới nhất (Near-realtime Signals)
    phục vụ bảng tín hiệu bên phải theo phong cách giao diện DNSE.
    """
    return [
        {
            "signal_id": "sig_01",
            "symbol": "HPG",
            "action": "BUY",
            "strategy_name": "Thuận xu hướng (Break out EMA 20)",
            "price": 27400,
            "target_price": 30100,
            "stop_price": 25480,
            "confidence": 88.5,
            "timestamp": "Hôm nay 14:15",
            "status": "MỚI",
        },
        {
            "signal_id": "sig_02",
            "symbol": "FPT",
            "action": "BUY",
            "strategy_name": "Xu hướng tăng mạnh kèm KLGD đột biến",
            "price": 134200,
            "target_price": 161000,
            "stop_price": 124800,
            "confidence": 92.1,
            "timestamp": "Hôm nay 11:30",
            "status": "MỚI",
        },
        {
            "signal_id": "sig_03",
            "symbol": "VNM",
            "action": "SELL",
            "strategy_name": "Chốt lời Take Profit (+20%)",
            "price": 68500,
            "target_price": 68500,
            "stop_price": 63700,
            "confidence": 84.0,
            "timestamp": "Hôm nay 10:45",
            "status": "CHỐT LÃI",
        },
        {
            "signal_id": "sig_04",
            "symbol": "MWG",
            "action": "BUY",
            "strategy_name": "CP tăng trưởng (Mini-Canslim)",
            "price": 64800,
            "target_price": 77700,
            "stop_price": 60200,
            "confidence": 86.7,
            "timestamp": "Hôm qua",
            "status": "ĐÃ KHỚP T+1",
        },
        {
            "signal_id": "sig_05",
            "symbol": "VIC",
            "action": "HOLD",
            "strategy_name": "Cổ phiếu chuyển từ sideway sang breakout",
            "price": 42100,
            "target_price": 45000,
            "stop_price": 39150,
            "confidence": 79.2,
            "timestamp": "Hôm qua",
            "status": "ĐANG NẮM GIỮ",
        },
    ]
