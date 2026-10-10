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
) -> tuple[BacktestMetrics, pd.DataFrame, pd.DataFrame]:
    """
    Thuật toán mô phỏng giao dịch thực tế thị trường chứng khoán Việt Nam.

    Cơ chế chi tiết:
    1. Không nhìn trước tương lai: Tín hiệu sinh ra tại cuối phiên t, lệnh thực thi vào phiên t+1.
    2. Khớp lệnh tại Open_{t+1} (hoặc Close_{t+1}) có cộng/trừ tỷ lệ trượt giá (slippage).
    3. Kiểm soát thanh toán T+2: Theo dõi từng lô mua (PositionLot), chỉ cho phép bán khi
       phiên hiện tại >= phiên_mua + settlement_delay (mặc định 2 phiên).
    4. Khấu trừ chi phí thực tế: Phí mua (0.15%), Phí bán (0.15%), Thuế bán (0.10%).
    5. Khớp lệnh theo lô chẵn 100 cổ phiếu và bảo toàn số dư tiền mặt lẻ.
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

        # 1. Tín hiệu MUA (curr_sig == 2)
        if curr_sig == 2 and cash > (base_exec_price * lot_size):
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

        # 2. Tín hiệu BÁN (curr_sig == 0)
        elif curr_sig == 0 and len(inventory) > 0:
            settled_lots = [lot for lot in inventory if lot.settled_idx <= exec_idx]
            unsettled_lots = [lot for lot in inventory if lot.settled_idx > exec_idx]

            if len(settled_lots) > 0:
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
                        reason="SIGNAL_SELL",
                    )
                )
                trade_id_counter += 1
                inventory = unsettled_lots

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
) -> BacktestResult:
    """
    Giao diện chạy Backtest cấp cao hỗ trợ cả nhãn tín hiệu trực tiếp hoặc ma trận xác suất 3 lớp.
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
