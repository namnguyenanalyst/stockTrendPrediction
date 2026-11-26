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
import hashlib
from dataclasses import dataclass, field
import logging
from pathlib import Path
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
    settled_idx: int  # Afternoon settlement session; open execution must wait one further session.
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
    cagr_pct: float | None  # Annualized Return / CAGR (%)
    buy_and_hold_return_pct: float  # Lợi nhuận chiến lược Buy & Hold (%)
    excess_return_pct: float  # Lợi nhuận vượt trội so với Buy & Hold (alpha %)
    annualized_volatility_pct: float | None  # Độ biến động năm hóa (%)
    sharpe_ratio: float | None  # Tỷ số Sharpe năm hóa (với lãi suất phi rủi ro Rf)
    sortino_ratio: float | None  # Tỷ số Sortino năm hóa (độ biến động giảm giá Downside Dev)
    max_drawdown_pct: float  # Mức sụt giảm vốn lớn nhất từ đỉnh (MDD %)
    calmar_ratio: float | None  # Tỷ số Calmar (CAGR / MDD)
    var_95_pct: float | None  # Giá trị chịu rủi ro VaR 95% 1 ngày theo lịch sử (%)
    cvar_95_pct: float | None  # Kỳ vọng tổn thất vượt mức CVaR 95% (Expected Shortfall %)
    win_rate_pct: float | None  # Tỷ lệ lệnh có lãi Win Rate (%)
    profit_factor: float | None  # Hệ số lợi nhuận Profit Factor (Tổng lãi / Tổng lỗ)
    total_trades: int  # Tổng số vòng giao dịch đã đóng
    winning_trades: int  # Số vòng giao dịch có lãi
    losing_trades: int  # Số vòng giao dịch hòa/lỗ
    avg_trade_return_pct: float | None  # Tỷ suất sinh lời trung bình mỗi lệnh (%)
    best_trade_return_pct: float | None  # Lợi nhuận của lệnh thắng lớn nhất (%)
    worst_trade_return_pct: float | None  # Mức lỗ của lệnh lỗ lớn nhất (%)
    avg_holding_days: float | None  # Thời gian nắm giữ trung bình mỗi lệnh (ngày)
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


def _data_fingerprint(frame: pd.DataFrame) -> str:
    """Content fingerprint; pandas version is recorded in simulation configuration."""
    digest = hashlib.sha256(str(list(frame.columns)).encode())
    digest.update(pd.util.hash_pandas_object(frame, index=False).to_numpy().tobytes())
    return digest.hexdigest()


def _load_training_provenance(models_dir: Path, horizon: int = 3) -> dict[str, Any]:
    """Read-only provenance summary from production_training_info_t{horizon}.json if present."""
    info_path = models_dir / f"production_training_info_t{horizon}.json"
    if not info_path.exists():
        return {}
    try:
        import json
        data = json.loads(info_path.read_text(encoding="utf-8"))
        return {
            "training_cutoff_date": data.get("latest_market_date"),
            "artifact_timestamp": data.get("timestamp"),
            "val_buffer_days": data.get("val_buffer_days"),
            "purged_horizon_days": data.get("horizon_days"),
        }
    except Exception:
        return {}


def _round_metric(value: float | None, digits: int = 2) -> float | None:
    """JSON-safe metrics: undefined and nonfinite values are null, never sentinels."""
    return round(float(value), digits) if value is not None and np.isfinite(value) else None


def _display_metric(value: float | None, digits: int = 2) -> str:
    return f"{value:.{digits}f}" if value is not None and np.isfinite(value) else "N/A"


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
    equity_series = pd.Series(equity_series, dtype=float).reset_index(drop=True)
    if (equity_series.empty or not np.isfinite(equity_series).all()
            or (equity_series < 0).any() or (equity_series.iloc[:-1] <= 0).any()):
        raise ValueError("Equity must be nonempty and finite, with positive pre-terminal values.")
    if not np.isfinite(initial_capital) or initial_capital <= 0:
        raise ValueError("initial_capital must be positive and finite.")
    if not np.isfinite(risk_free_rate) or risk_free_rate <= -1:
        raise ValueError("risk_free_rate must be finite and greater than -1.")
    # Standalone callers may supply EOD observations without the pre-investment point.
    if equity_series.iloc[0] != initial_capital:
        equity_series = pd.concat([pd.Series([initial_capital]), equity_series], ignore_index=True)
    final_equity = float(equity_series.iloc[-1])
    n_days = len(equity_series)
    total_return_pct = (
        ((final_equity - initial_capital) / initial_capital) * 100.0
        if initial_capital > 0
        else 0.0
    )

    # 1. CAGR (Annualized Return)
    if final_equity > 0 and n_days > 1 and initial_capital > 0:
        with np.errstate(over="ignore"):
            cagr_pct = float(np.expm1(np.log(final_equity / initial_capital) * (252.0 / (n_days - 1))) * 100)
    else:
        cagr_pct = -100.0 if final_equity <= 0 else None

    # 2. Lợi suất hàng ngày & Lãi suất phi rủi ro theo ngày
    daily_returns = equity_series.pct_change(fill_method=None).dropna()
    rf_daily = risk_free_rate / 252.0

    # 3. Độ biến động năm hóa
    ann_volatility_pct = (
        float(daily_returns.std() * np.sqrt(252.0) * 100.0) if len(daily_returns) > 1 else None
    )

    # 4. Tỷ số Sharpe năm hóa
    excess_returns = daily_returns - rf_daily
    if len(daily_returns) > 1 and daily_returns.std() > 1e-9:
        sharpe_ratio = float(excess_returns.mean() / daily_returns.std() * np.sqrt(252.0))
    else:
        sharpe_ratio = None

    # 5. Tỷ số Sortino năm hóa (Downside Deviation so với rf_daily)
    downside_std = np.sqrt(np.mean(np.minimum(excess_returns, 0.0)**2)) if len(excess_returns) else 0.0
    if downside_std > 1e-9:
        sortino_ratio = float(excess_returns.mean() / downside_std * np.sqrt(252.0))
    else:
        sortino_ratio = None

    # 6. Maximum Drawdown (MDD)
    peaks = np.maximum.accumulate(equity_series.values)
    drawdowns = (equity_series.values - peaks) / np.where(peaks > 0, peaks, 1.0)
    max_drawdown_pct = float(np.min(drawdowns) * 100.0) if len(drawdowns) > 0 else 0.0
    abs_mdd = abs(max_drawdown_pct)

    # 7. Calmar Ratio (CAGR / MDD)
    calmar_ratio = float(cagr_pct / abs_mdd) if abs_mdd > 1e-6 and cagr_pct is not None else None

    # 8. VaR 95% và CVaR 95% (Historical Daily)
    if len(daily_returns) > 10:
        p5 = float(np.percentile(daily_returns, 5))
        var_95_pct = float(-p5 * 100.0)
        tail_returns = daily_returns[daily_returns <= p5]
        cvar_95_pct = float(-tail_returns.mean() * 100.0) if len(tail_returns) > 0 else var_95_pct
    else:
        var_95_pct, cvar_95_pct = None, None

    # 9. Thống kê lệnh đóng (SELL orders)
    closed_trades = [t for t in trades if t.order_type == "SELL" and t.realized_pnl is not None]
    total_trades_count = len(closed_trades)
    winning_trades = [t for t in closed_trades if t.realized_pnl > 0]
    losing_trades = [t for t in closed_trades if t.realized_pnl <= 0]
    win_rate_pct = (
        (len(winning_trades) / total_trades_count * 100.0) if total_trades_count > 0 else None
    )

    gross_profit = sum(t.realized_pnl for t in winning_trades)
    gross_loss = abs(sum(t.realized_pnl for t in losing_trades))
    if gross_loss > 1e-6:
        profit_factor = float(gross_profit / gross_loss)
    elif gross_profit > 1e-6:
        profit_factor = None
    else:
        profit_factor = None

    trade_returns = [
        t.realized_return_pct for t in closed_trades if t.realized_return_pct is not None
    ]
    avg_trade_return_pct = float(np.mean(trade_returns)) if trade_returns else None
    best_trade_return_pct = float(np.max(trade_returns)) if trade_returns else None
    worst_trade_return_pct = float(np.min(trade_returns)) if trade_returns else None

    holding_durations = [t.holding_days for t in closed_trades if t.holding_days is not None]
    avg_holding_days = float(np.mean(holding_durations)) if holding_durations else None

    total_fees = sum(t.fee for t in trades)
    total_taxes = sum(t.tax for t in trades)
    total_costs = total_fees + total_taxes

    cost_impact_pct = (total_costs / initial_capital) * 100.0 if initial_capital > 0 else 0.0

    return BacktestMetrics(
        initial_capital=initial_capital,
        final_equity=round(final_equity, 2),
        total_return_pct=round(total_return_pct, 2),
        cagr_pct=_round_metric(cagr_pct, 2),
        buy_and_hold_return_pct=round(buy_and_hold_return_pct, 2),
        excess_return_pct=round(total_return_pct - buy_and_hold_return_pct, 2),
        annualized_volatility_pct=_round_metric(ann_volatility_pct, 2),
        sharpe_ratio=_round_metric(sharpe_ratio, 4),
        sortino_ratio=_round_metric(sortino_ratio, 4),
        max_drawdown_pct=round(abs_mdd, 2),
        calmar_ratio=_round_metric(calmar_ratio, 4),
        var_95_pct=_round_metric(var_95_pct, 2),
        cvar_95_pct=_round_metric(cvar_95_pct, 2),
        win_rate_pct=_round_metric(win_rate_pct, 2),
        profit_factor=_round_metric(profit_factor, 4),
        total_trades=total_trades_count,
        winning_trades=len(winning_trades),
        losing_trades=len(losing_trades),
        avg_trade_return_pct=_round_metric(avg_trade_return_pct, 2),
        best_trade_return_pct=_round_metric(best_trade_return_pct, 2),
        worst_trade_return_pct=_round_metric(worst_trade_return_pct, 2),
        avg_holding_days=_round_metric(avg_holding_days, 1),
        total_fees_paid=round(total_fees, 2),
        total_taxes_paid=round(total_taxes, 2),
        total_costs=round(total_costs, 2),
        cost_impact_pct=round(cost_impact_pct, 2),
        equity_curve=[round(x, 2) for x in equity_series.tolist()],
    )


def trading_prices_vnd(df: pd.DataFrame, price_unit: str) -> pd.DataFrame:
    """Convert ingestion prices explicitly; the cash engine always operates in VND."""
    if price_unit not in ("VND", "kVND"):
        raise ValueError("price_unit must be VND or kVND.")
    result = df.copy()
    if price_unit == "kVND":
        result[["Open", "High", "Low", "Close"]] *= 1000.0
    return result


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
       Close phiên_mua + settlement_delay, hoặc Open phiên tiếp theo (T+2 về buổi chiều).
    4. Tích hợp Quản trị rủi ro chủ động (DNSE Risk Rules):
       - Stop Loss (Cắt lỗ cố định): Bán ngay khi chạm ngưỡng lỗ quy định.
       - Take Profit (Chốt lời mục tiêu): Chốt lãi khi đạt lợi nhuận kỳ vọng.
       - Trailing Stop (Bảo toàn lãi): Kích hoạt bán khi sụt giảm từ đỉnh giá cao nhất.
       - Tín hiệu AI: Đóng vị thế khi mô hình dự báo đảo chiều (SIGNAL_SELL).
    5. Khấu trừ chi phí thực tế: Phí mua (0.15%), Phí bán (0.15%), Thuế bán (0.10%).
    6. Khớp lệnh theo lô chẵn 100 cổ phiếu và bảo toàn số dư tiền mặt lẻ.
    """
    # Validate at the engine boundary, including callers outside the REST API.
    if not np.isfinite(initial_capital) or initial_capital <= 0:
        raise ValueError("initial_capital must be positive and finite.")
    for name, value in (("fee_rate", fee_rate), ("tax_rate", tax_rate),
                        ("slippage_rate", slippage_rate)):
        if not np.isfinite(value) or not 0 <= value < 1:
            raise ValueError(f"{name} must be finite and in [0, 1).")
    if fee_rate + tax_rate >= 1:
        raise ValueError("Combined selling costs must be less than 1.")
    for name, value, minimum in (("lot_size", lot_size, 1),
                                 ("settlement_delay", settlement_delay, 0)):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}.")
    if not np.isfinite(risk_free_rate) or risk_free_rate <= -1:
        raise ValueError("risk_free_rate must be finite and greater than -1.")
    for name, value in (("take_profit_pct", take_profit_pct),
                        ("stop_loss_pct", stop_loss_pct),
                        ("trailing_stop_pct", trailing_stop_pct)):
        if value is not None and (not np.isfinite(value) or value < 0):
            raise ValueError(f"{name} must be finite and nonnegative.")
    required = {"Date", "Open", "Close"}
    if not required.issubset(df.columns):
        raise ValueError("Market data requires Date, Open and Close.")
    price_columns = [c for c in ("Open", "High", "Low", "Close") if c in df]
    prices = df[price_columns].to_numpy(dtype=float)
    if not np.isfinite(prices).all() or (prices <= 0).any():
        raise ValueError("Market prices must be positive and finite.")
    if "High" in df and (df["High"] < df[["Open", "Close"]].max(axis=1)).any():
        raise ValueError("High must cover Open and Close.")
    if "Low" in df and (df["Low"] > df[["Open", "Close"]].min(axis=1)).any():
        raise ValueError("Low must cover Open and Close.")
    if "Volume" in df:
        volume = df["Volume"].to_numpy(dtype=float)
        if not np.isfinite(volume).all() or (volume < 0).any():
            raise ValueError("Volume must be finite and nonnegative.")
    signals = np.asarray(signals)
    if signals.ndim != 1 or not np.isin(signals, [0, 1, 2]).all():
        raise ValueError("signals must be a one-dimensional array of classes 0, 1, 2.")
    if df.empty or not pd.to_datetime(df["Date"]).is_monotonic_increasing:
        raise ValueError("Market rows must be nonempty and sorted (tăng dần) by Date.")
    if pd.to_datetime(df["Date"]).duplicated().any():
        raise ValueError("Market dates must be unique.")
    if execution_price not in ("open", "close") or settlement_delay < 0:
        raise ValueError("Invalid execution_price or settlement_delay.")
    df_sorted = df.reset_index(drop=True)
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
    volumes = df_sorted["Volume"].values.astype(float) if "Volume" in df_sorted else None

    cash = float(initial_capital)
    inventory: list[PositionLot] = []
    receivables: list[tuple[int, float]] = []  # settlement session, net proceeds
    trades: list[TradeRecord] = []
    trade_id_counter = 1

    equity_records = [
        {
            "Date": dates[0],
            "Cash": cash,
            "Receivables": 0.0,
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

        # No cash advance: T+2 proceeds become spendable after settlement, not at sale.
        available_idx = exec_idx - int(execution_price == "open" and settlement_delay > 0)
        cash += sum(amount for due, amount in receivables if due <= available_idx)
        receivables = [(due, amount) for due, amount in receivables if due > available_idx]
        base_exec_price = opens[exec_idx] if execution_price == "open" else closes[exec_idx]

        # Close-triggered orders are decided after the previous bar, then executed
        # at the next close. Open mode is a standing opening-price risk rule;
        # neither mode infers an intraday High/Low path from a daily candle.
        risk_price = base_exec_price if execution_price == "open" else closes[i]
        # Cập nhật giá đỉnh cao nhất cho các lô đang nắm giữ (phục vụ Trailing Stop)
        for lot in inventory:
            if risk_price > lot.highest_price:
                lot.highest_price = risk_price

        # Kiểm tra điều kiện bán đối với các lô đã về tài khoản (T+2)
        # T+2 settles in the afternoon; an open-only engine must wait another bar.
        available_idx = exec_idx - int(execution_price == "open" and settlement_delay > 0)
        settled_lots = [lot for lot in inventory if lot.settled_idx <= available_idx]
        unsettled_lots = [lot for lot in inventory if lot.settled_idx > available_idx]

        should_sell = False
        sell_reason = "SIGNAL_SELL"

        if len(settled_lots) > 0:
            # 1. Kiểm tra Cắt lỗ (Stop Loss)
            if stop_loss_pct is not None and stop_loss_pct > 0:
                for lot in settled_lots:
                    ret_from_buy = (risk_price - lot.buy_price) / lot.buy_price
                    if ret_from_buy <= -abs(stop_loss_pct):
                        should_sell = True
                        sell_reason = "STOP_LOSS"
                        break

            # 2. Kiểm tra Chốt lời (Take Profit)
            if not should_sell and take_profit_pct is not None and take_profit_pct > 0:
                for lot in settled_lots:
                    ret_from_buy = (risk_price - lot.buy_price) / lot.buy_price
                    if ret_from_buy >= abs(take_profit_pct):
                        should_sell = True
                        sell_reason = "TAKE_PROFIT"
                        break

            # 3. Kiểm tra Trailing Stop (Bảo toàn lãi khi giảm từ đỉnh)
            if not should_sell and trailing_stop_pct is not None and trailing_stop_pct > 0:
                for lot in settled_lots:
                    if lot.highest_price > lot.buy_price:
                        drop_from_peak = (lot.highest_price - risk_price) / lot.highest_price
                        if drop_from_peak >= abs(trailing_stop_pct):
                            should_sell = True
                            sell_reason = "TRAILING_STOP"
                            break

            # 4. Kiểm tra Tín hiệu Bán thông thường từ AI (curr_sig == 0)
            if not should_sell and curr_sig == 0:
                should_sell = True
                sell_reason = "SIGNAL_SELL"

        # Thực thi BÁN nếu thỏa mãn điều kiện và có hàng T+2
        is_liquid_session = volumes is None or volumes[exec_idx] > 0
        if is_liquid_session and should_sell and len(settled_lots) > 0:
            sell_shares = sum(lot.shares for lot in settled_lots)
            p_sell = base_exec_price * (1.0 - slippage_rate)
            gross = sell_shares * p_sell
            fee = gross * fee_rate
            tax = gross * tax_rate
            net_proceeds = gross - fee - tax
            if settlement_delay == 0:
                cash += net_proceeds
            else:
                receivables.append((exec_idx + settlement_delay, net_proceeds))

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
        elif is_liquid_session and curr_sig == 2 and cash >= (base_exec_price * lot_size):
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

        # Afternoon settlement is reflected in EOD cash, but cannot fund that day's open.
        cash += sum(amount for due, amount in receivables if due <= exec_idx)
        receivables = [(due, amount) for due, amount in receivables if due > exec_idx]
        pending_cash = sum(amount for _, amount in receivables)
        # Định giá tài sản cuối ngày exec_idx
        shares_held = sum(lot.shares for lot in inventory)
        pos_val = shares_held * closes[exec_idx]
        total_eq = cash + pending_cash + pos_val
        equity_records.append(
            {
                "Date": exec_date,
                "Cash": cash,
                "Receivables": pending_cash,
                "Shares": shares_held,
                "Position_Value": pos_val,
                "Total_Equity": total_eq,
            }
        )

    # Đóng vị thế vào ngày cuối cùng nếu close_at_end=True
    final_settled = [lot for lot in inventory if lot.settled_idx <= n_bars - 1]
    if close_at_end and final_settled:
        final_idx = n_bars - 1
        final_date = dates[final_idx]
        final_close = closes[final_idx] * (1.0 - slippage_rate)
        sell_shares = sum(lot.shares for lot in final_settled)

        gross = sell_shares * final_close
        fee = gross * fee_rate
        tax = gross * tax_rate
        net_proceeds = gross - fee - tax
        if settlement_delay == 0:
            cash += net_proceeds
        else:
            receivables.append((final_idx + settlement_delay, net_proceeds))

        total_cost_basis = sum(lot.cost_basis for lot in final_settled)
        realized_pnl = net_proceeds - total_cost_basis
        realized_ret_pct = (
            (realized_pnl / total_cost_basis * 100.0) if total_cost_basis > 0 else 0.0
        )
        avg_holding = (
            sum((final_idx - lot.buy_idx) * lot.shares for lot in final_settled) / sell_shares
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
        inventory = [lot for lot in inventory if lot.settled_idx > final_idx]

        # Cập nhật giá trị phiên cuối
        equity_records[-1]["Cash"] = cash
        equity_records[-1]["Shares"] = sum(lot.shares for lot in inventory)
        equity_records[-1]["Position_Value"] = equity_records[-1]["Shares"] * closes[final_idx]
        equity_records[-1]["Receivables"] = sum(amount for _, amount in receivables)
        equity_records[-1]["Total_Equity"] = (
            cash + equity_records[-1]["Receivables"] + equity_records[-1]["Position_Value"]
        )

    eq_df = pd.DataFrame(equity_records)
    eq_df["Open"] = opens
    eq_df["High"] = (
        df_sorted["High"].values.astype(float) if "High" in df_sorted.columns else opens
    )
    eq_df["Low"] = df_sorted["Low"].values.astype(float) if "Low" in df_sorted.columns else opens
    eq_df["Close"] = closes

    trades_df = pd.DataFrame([t.__dict__ for t in trades]) if trades else pd.DataFrame()

    # Tính chiến lược đối chứng Mua & Nắm giữ (Buy & Hold)
    entry_prices = opens if execution_price == "open" else closes
    p_bh_buy = entry_prices[min(1, n_bars - 1)] * (1.0 + slippage_rate)
    bh_shares_max = int((initial_capital // (p_bh_buy * (1.0 + fee_rate)) // lot_size) * lot_size)
    bh_cash = initial_capital - (bh_shares_max * p_bh_buy * (1.0 + fee_rate))
    bh_series = [initial_capital]

    for j in range(1, n_bars):
        if j == n_bars - 1 and close_at_end and j >= 1 + settlement_delay:
            final_p = closes[j] * (1.0 - slippage_rate)
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
    for name, value in (("buy_prob_threshold", buy_prob_threshold),
                        ("sell_prob_threshold", sell_prob_threshold)):
        if not np.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"{name} must be finite and in [0, 1].")
    if probabilities is not None:
        probabilities = np.asarray(probabilities, dtype=float)
        if probabilities.shape != (len(df), 3):
            raise ValueError("probabilities must have shape (number of market rows, 3).")
        if (not np.isfinite(probabilities).all() or (probabilities < 0).any()
                or (probabilities > 1).any()
                or not np.allclose(probabilities.sum(axis=1), 1, rtol=0, atol=1e-6)):
            raise ValueError("probabilities must be finite, in [0, 1] and sum to 1 per row.")
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
        "data_fingerprint": _data_fingerprint(df),
        "signals_fingerprint": _data_fingerprint(pd.DataFrame({"signal": signals})),
        "pandas_version": pd.__version__,
        "initial_capital": initial_capital,
        "fee_rate": fee_rate,
        "tax_rate": tax_rate,
        "slippage_rate": slippage_rate,
        "lot_size": lot_size,
        "settlement_delay": settlement_delay,
        "execution_price": execution_price,
        "close_at_end": close_at_end,
        "cash_settlement": "no_advance_afternoon_T_plus_delay",
        "settlement_regime_effective_from": "2022-08-29",
        "settlement_regime_warning": (
            "Simulation includes dates before 2022-08-29 when afternoon T+2 settlement was not yet effective."
            if str(pd.to_datetime(df["Date"].iloc[0]).date()) < "2022-08-29"
            else None
        ),
        "price_adjustment_status": "unverified",
        "corporate_actions_modeled": False,
        "dividend_modeled": False,
        "risk_execution": "standing_open_checks" if execution_price == "open" else "previous_close_next_close",
        "intraday_stops": False,
        "price_unit": "VND",
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
    """Mô phỏng tín hiệu ngẫu nhiên độc lập theo xác suất lớp được chỉ định."""
    rng = np.random.default_rng(seed)
    n_bars = len(df)
    classes = [0, 1, 2]
    signals = rng.choice(classes, size=n_bars, p=list(class_probs))

    return run_backtest(
        df=df,
        signals=signals,
        symbol=symbol,
        initial_capital=initial_capital,
        strategy_name=f"Random_Baseline_Seed{seed}",
        **kwargs,
    )


def monte_carlo_tail_probability(samples, observed) -> float:
    """Plus-one right-tail estimate, conditional on the specified simulation null."""
    values = np.asarray(samples, dtype=float)
    if not len(values) or not np.isfinite(values).all() or not np.isfinite(observed):
        raise ValueError("Monte Carlo statistics must be finite and nonempty.")
    return float((1 + np.count_nonzero(values >= observed)) / (len(values) + 1))


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
    Mô phỏng n_simulations đường tín hiệu độc lập theo phân phối lớp chỉ định.
    Phân vị 5% và 95% mô tả phân phối đối chứng, không phải khoảng tin cậy
    của hiệu năng AI. Xác suất đuôi chỉ có ý nghĩa dưới giả thuyết đối chứng này.
    """
    probabilities = np.asarray(class_probs, dtype=float)
    if (not isinstance(n_simulations, (int, np.integer)) or n_simulations < 1
            or probabilities.shape != (3,) or not np.isfinite(probabilities).all()
            or (probabilities < 0).any() or not np.isclose(probabilities.sum(), 1)):
        raise ValueError("Positive simulation count and three valid class probabilities required.")
    rng = np.random.default_rng(seed)
    n_bars = len(df)
    classes = [0, 1, 2]

    mc_returns = []
    mc_sharpes = []
    mc_mdds = []

    for _ in range(n_simulations):
        rand_signals = rng.choice(classes, size=n_bars, p=probabilities)
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

    arr_ret = np.array(mc_returns)
    arr_shp = np.array([value for value in mc_sharpes if value is not None], dtype=float)
    arr_mdd = np.array(mc_mdds)

    out = {
        "symbol": symbol,
        "n_simulations": n_simulations,
        "seed": seed,
        "null_model": "iid_class_signals",
        "class_probabilities": probabilities.tolist(),
        "p_value_method": "plus_one_right_tail_conditional_on_iid_null",
        "simulations": [{"roi": roi, "sharpe": sharpe, "mdd": mdd}
                        for roi, sharpe, mdd in zip(mc_returns, mc_sharpes, mc_mdds)],
        "roi_stats": {
            "mean": round(float(arr_ret.mean()), 2),
            "std": round(float(arr_ret.std()), 2),
            "p5": round(float(np.percentile(arr_ret, 5)), 2),
            "median": round(float(np.median(arr_ret)), 2),
            "p95": round(float(np.percentile(arr_ret, 95)), 2),
        },
        "sharpe_stats": {
            "defined_count": len(arr_shp),
            "undefined_count": n_simulations - len(arr_shp),
            "distribution": "conditional_on_defined_sharpe",
            "mean": _round_metric(arr_shp.mean(), 4) if len(arr_shp) else None,
            "std": _round_metric(arr_shp.std(), 4) if len(arr_shp) else None,
            "p5": _round_metric(np.percentile(arr_shp, 5), 4) if len(arr_shp) else None,
            "median": _round_metric(np.median(arr_shp), 4) if len(arr_shp) else None,
            "p95": _round_metric(np.percentile(arr_shp, 95), 4) if len(arr_shp) else None,
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
        p_val_ret = monte_carlo_tail_probability(arr_ret, ai_ret)
        # Do not silently drop no-trade/constant-return simulations from a p-value.
        p_val_shp = (monte_carlo_tail_probability(arr_shp, ai_shp)
                     if ai_shp is not None and len(arr_shp) == n_simulations else None)
        out["ai_comparison"] = {
            "ai_roi": ai_ret,
            "ai_sharpe": ai_shp,
            "p_value_roi": round(p_val_ret, 4),
            "p_value_sharpe": _round_metric(p_val_shp, 4),
            "statistically_significant_at_5pct": bool(p_val_shp < 0.05) if p_val_shp is not None else None,
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
    fee_rate: float = TRANSACTION_FEE_RATE,
    tax_rate: float = TAX_RATE,
    lot_size: int = LOT_SIZE,
    settlement_delay: int = 2,
    execution_price: str = "open",
    buy_prob_threshold: float = 0.40,
    sell_prob_threshold: float = 0.40,
    take_profit_pct: float | None = None,
    stop_loss_pct: float | None = None,
    trailing_stop_pct: float | None = None,
    val_buffer_days: int = 40,
    price_unit: str = "kVND",
) -> BacktestResult:
    """
    Legacy entry point: simulate on the model-selection Validation Buffer (not independent OOS)
    sử dụng mô hình AI và Scaler đã lưu trong models/.
    """
    from vn_stock.config import (
        DEFAULT_HORIZON_DAYS,
        DEFAULT_SEQ_LENGTH,
        DEFAULT_TREND_THRESHOLD_3D,
    )
    from vn_stock.data_ingestion import load_panel_dataset
    from vn_stock.features import (
        ALL_FEATURE_COLS,
        compute_features_per_symbol,
    )
    from vn_stock.splitting_data import (
        apply_study_window,
        create_multi_day_labels,
    )

    clean_sym = symbol.upper()

    df_raw = load_panel_dataset()
    df_feat = compute_features_per_symbol(df_raw, drop_na=True)
    df_study = apply_study_window(df_feat)
    df_labeled = create_multi_day_labels(
        df_study, horizon=DEFAULT_HORIZON_DAYS, threshold=DEFAULT_TREND_THRESHOLD_3D
    )
    validation_dates = np.sort(df_labeled["Date"].unique())[-val_buffer_days:]
    sym_df = df_labeled[(df_labeled["Symbol"] == clean_sym)
                        & df_labeled["Date"].isin(validation_dates)].sort_values("Date").reset_index(drop=True)
    if sym_df.empty:
        raise ValueError(f"Không tìm thấy dữ liệu cho mã {clean_sym} trong tập kiểm thử.")

    from vn_stock.features import create_multivariate_sequences, transform_model_features
    from vn_stock.modeling.predict import load_prediction_snapshot

    model, scaler, info = load_prediction_snapshot(model_type, models_dir)
    # Split construction identifies dates only; inference must use the persisted scaler.
    raw_symbol = sym_df.copy()
    sym_scaled = transform_model_features(raw_symbol, scaler)
    sym_df = raw_symbol.reset_index(drop=True)
    if model_type.lower() in ("lightgbm", "lgb"):
        probs = (model.predict_proba(sym_scaled[ALL_FEATURE_COLS])
                 if hasattr(model, "predict_proba") else model.predict(sym_scaled[ALL_FEATURE_COLS]))
    elif model_type.lower() == "lstm":
        import torch
        sequence_length = info.get("seq_length", DEFAULT_SEQ_LENGTH)
        warm = df_feat[(df_feat["Symbol"] == clean_sym)
                       & (df_feat["Date"] < sym_df["Date"].min())].tail(sequence_length - 1)
        warm = transform_model_features(warm, scaler)
        xs, _ = create_multivariate_sequences(
            sym_scaled, warm, ALL_FEATURE_COLS, sequence_length,
        )
        if len(xs) != len(sym_df):
            raise ValueError("Insufficient warm-up for validation backtest.")
        with torch.no_grad():
            inputs = torch.from_numpy(np.ascontiguousarray(xs)).to(next(model.parameters()).device)
            probs = model.predict_proba(inputs).cpu().numpy()
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

    result = run_backtest(
        df=trading_prices_vnd(sym_df, price_unit),
        probabilities=probs,
        buy_prob_threshold=buy_prob_threshold,
        sell_prob_threshold=sell_prob_threshold,
        symbol=clean_sym,
        initial_capital=initial_capital,
        fee_rate=fee_rate,
        tax_rate=tax_rate,
        slippage_rate=slippage_rate,
        lot_size=lot_size,
        settlement_delay=settlement_delay,
        execution_price=execution_price,
        strategy_name=f"AI_{model_type.upper()}_VALIDATION",
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
        trailing_stop_pct=trailing_stop_pct,
    )
    result.config.update({"model_type": model_type.lower(), "model_info": info,
                          "training_provenance": _load_training_provenance(models_dir),
                          "evaluation_kind": "model_selection_validation_simulation",
                          "independent_oos": False,
                          "leakage_warning": "Uses model-selection validation buffer with persisted production artifact; not independent OOS.",
                          "input_price_unit": price_unit,
                          "buy_prob_threshold": buy_prob_threshold,
                          "sell_prob_threshold": sell_prob_threshold})
    return result



def backtest_all_symbols(
    symbols: list[str] | str | None = None,
    model_type: str = "lightgbm",
    initial_capital: float = INITIAL_CAPITAL,
    slippage_rate: float = 0.0005,
) -> pd.DataFrame:
    """Chạy Backtest OOS đồng loạt trên danh mục cổ phiếu (VN30 hoặc CORE) và xuất bảng tổng hợp đối chứng."""
    from vn_stock.config import DEFAULT_SYMBOLS, VN30_SYMBOLS

    if symbols is None or (isinstance(symbols, str) and symbols.upper() in ["VN30", "ALL"]):
        target_symbols = list(VN30_SYMBOLS)
    elif isinstance(symbols, str) and symbols.upper() == "CORE":
        target_symbols = list(DEFAULT_SYMBOLS)
    elif isinstance(symbols, str):
        target_symbols = [symbols.upper()]
    elif isinstance(symbols, list):
        target_symbols = [s.upper() for s in symbols]
    else:
        target_symbols = list(VN30_SYMBOLS)

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
    """Prepare indicators using the shared implementation."""
    from vn_stock.chart_indicators import compute_chart_indicators

    return compute_chart_indicators(df)


def _get_foreign_buy_val(df: pd.DataFrame, idx: int, meta: dict[str, Any] | None) -> float:
    if "Foreign_Net_Val" in df.columns:
        return float(df["Foreign_Net_Val"].iloc[idx])
    if "Foreign_Buy_Val" in df.columns and "Foreign_Sell_Val" in df.columns:
        return float(df["Foreign_Buy_Val"].iloc[idx] - df["Foreign_Sell_Val"].iloc[idx])
    raise ValueError("Historical order flow observations are required; no volume proxy is allowed.")


def _get_foreign_buy_vol(df: pd.DataFrame, idx: int, meta: dict[str, Any] | None) -> float:
    if "Foreign_Net_Vol" in df.columns:
        return float(df["Foreign_Net_Vol"].iloc[idx])
    if "Foreign_Buy_Vol" in df.columns and "Foreign_Sell_Vol" in df.columns:
        return float(df["Foreign_Buy_Vol"].iloc[idx] - df["Foreign_Sell_Vol"].iloc[idx])
    raise ValueError("Historical order flow observations are required; no volume proxy is allowed.")


def _get_prop_buy_val(df: pd.DataFrame, idx: int, meta: dict[str, Any] | None) -> float:
    if "Prop_Net_Val" in df.columns:
        return float(df["Prop_Net_Val"].iloc[idx])
    if "Prop_Buy_Val" in df.columns and "Prop_Sell_Val" in df.columns:
        return float(df["Prop_Buy_Val"].iloc[idx] - df["Prop_Sell_Val"].iloc[idx])
    raise ValueError("Historical order flow observations are required; no volume proxy is allowed.")


def _get_prop_buy_vol(df: pd.DataFrame, idx: int, meta: dict[str, Any] | None) -> float:
    if "Prop_Net_Vol" in df.columns:
        return float(df["Prop_Net_Vol"].iloc[idx])
    if "Prop_Buy_Vol" in df.columns and "Prop_Sell_Vol" in df.columns:
        return float(df["Prop_Buy_Vol"].iloc[idx] - df["Prop_Sell_Vol"].iloc[idx])
    raise ValueError("Historical order flow observations are required; no volume proxy is allowed.")


def _get_foreign_sell_val(df: pd.DataFrame, idx: int, meta: dict[str, Any] | None) -> float:
    if "Foreign_Sell_Val" in df.columns and "Foreign_Buy_Val" in df.columns:
        return float(df["Foreign_Sell_Val"].iloc[idx] - df["Foreign_Buy_Val"].iloc[idx])
    if "Foreign_Net_Val" in df.columns:
        return -float(df["Foreign_Net_Val"].iloc[idx])
    raise ValueError("Historical order flow observations are required; no volume proxy is allowed.")


def _get_prop_sell_vol(df: pd.DataFrame, idx: int, meta: dict[str, Any] | None) -> float:
    if "Prop_Sell_Vol" in df.columns and "Prop_Buy_Vol" in df.columns:
        return float(df["Prop_Sell_Vol"].iloc[idx] - df["Prop_Buy_Vol"].iloc[idx])
    if "Prop_Net_Vol" in df.columns:
        return -float(df["Prop_Net_Vol"].iloc[idx])
    raise ValueError("Historical order flow observations are required; no volume proxy is allowed.")


def _get_foreign_sell_vol(df: pd.DataFrame, idx: int, meta: dict[str, Any] | None) -> float:
    if "Foreign_Sell_Vol" in df.columns and "Foreign_Buy_Vol" in df.columns:
        return float(df["Foreign_Sell_Vol"].iloc[idx] - df["Foreign_Buy_Vol"].iloc[idx])
    if "Foreign_Net_Vol" in df.columns:
        return -float(df["Foreign_Net_Vol"].iloc[idx])
    raise ValueError("Historical order flow observations are required; no volume proxy is allowed.")


def _get_prop_sell_val(df: pd.DataFrame, idx: int, meta: dict[str, Any] | None) -> float:
    if "Prop_Sell_Val" in df.columns and "Prop_Buy_Val" in df.columns:
        return float(df["Prop_Sell_Val"].iloc[idx] - df["Prop_Buy_Val"].iloc[idx])
    if "Prop_Net_Val" in df.columns:
        return -float(df["Prop_Net_Val"].iloc[idx])
    raise ValueError("Historical order flow observations are required; no volume proxy is allowed.")


def _historical_fundamental(df: pd.DataFrame, idx: int, column: str) -> float:
    """Read a historical as-of value; current symbol metadata is not a time series.

    Caller must align observations as-of their publication time, in Vietnam local time.
    No fabricated fallback or backwards fill is permitted.
    """
    if column not in df or "Fundamental_Available_At" not in df:
        raise ValueError(f"Historical point-in-time {column} and Fundamental_Available_At are required.")
    available = pd.Timestamp(df["Fundamental_Available_At"].iloc[idx])
    close_time = pd.Timestamp(df["Date"].iloc[idx]).normalize() + pd.Timedelta(hours=15)
    if pd.isna(available) or available > close_time:
        raise ValueError(f"Historical {column} was not available at signal time (future publication).")
    value = float(df[column].iloc[idx])
    if not np.isfinite(value):
        raise ValueError(f"Historical {column} must be finite.")
    return value


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

    for rule_name, rules in (("buy_rules", buy_rules), ("sell_rules", sell_rules)):
        mc = rules.get("market_condition")
        if mc not in (None, "all"):
            raise ValueError(f"{rule_name}.market_condition='{mc}' is not supported without historical VNINDEX regime data.")

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
        "foreign_net_buy_val",
        "prop_net_vol",
        "prop_net_buy_vol",
        "foreign_net_vol",
        "foreign_net_buy_vol",
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
        "prop_net_buy_val",
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
                pb_est = _historical_fundamental(df, i, "pb")
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
                cap_est = _historical_fundamental(df, i, "market_cap")
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
                    raise ValueError(f"Unsupported MA indicator column: {col}")

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
                    raise ValueError(f"Unsupported MA operator: {op}")

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
                    elif op == "=":
                        active_buy_flags.append(bool(abs(p0 - p1) < 1e-4))
                    else:
                        raise ValueError(f"Unsupported price_t0_operator: {op}")
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
                    raise ValueError(f"Unsupported EMA indicator column: {col}")

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
                    raise ValueError(f"Unsupported EMA operator: {op}")

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
                    raise ValueError(f"Unsupported MACD operator: {op}")

            # 11. ADX (14)
            if buy_rules.get("use_adx"):
                min_adx = float(buy_rules.get("min_adx") if buy_rules.get("min_adx") is not None else 0.0)
                max_adx = float(buy_rules.get("max_adx") if buy_rules.get("max_adx") is not None else 100.0)
                active_buy_flags.append(bool(min_adx <= df["ADX"].iloc[i] <= max_adx))

            # 12. RS
            if buy_rules.get("use_rs"):
                if "RS" not in df:
                    raise ValueError("Historical RS indicator is required.")
                min_rs = float(buy_rules.get("min_rs") if buy_rules.get("min_rs") is not None else 0.0)
                max_rs = float(buy_rules.get("max_rs") if buy_rules.get("max_rs") is not None else 100.0)
                rs_val = float(df["RS"].iloc[i])
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
                        if col in df:
                            return float(df[col].iloc[idx])
                        raise ValueError(f"Unsupported cross target column: {col}")
                    col = f"SMA{digits}" if digits else "SMA10"
                    if col in df:
                        return float(df[col].iloc[idx])
                    raise ValueError(f"Unsupported cross target column: {col}")

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
                    raise ValueError(f"Unsupported price_cross_operator: {op}")

            # 14. Bollinger Bands
            if buy_rules.get("use_bb"):
                active_buy_flags.append(bool(df["Close"].iloc[i] <= df["BB_Lower"].iloc[i] * 1.02))

            # 15. Financial & Fundamental Indicators
            if buy_rules.get("use_pe"):
                min_pe = float(buy_rules.get("min_pe") if buy_rules.get("min_pe") is not None else -100.0)
                max_pe = float(buy_rules.get("max_pe") if buy_rules.get("max_pe") is not None else 150.0)
                pe_est = _historical_fundamental(df, i, "pe")
                active_buy_flags.append(bool(min_pe <= pe_est <= max_pe))

            if buy_rules.get("use_ps"):
                min_ps = float(buy_rules.get("min_ps") if buy_rules.get("min_ps") is not None else 0.0)
                max_ps = float(buy_rules.get("max_ps") if buy_rules.get("max_ps") is not None else 20.0)
                ps_est = _historical_fundamental(df, i, "ps")
                active_buy_flags.append(bool(min_ps <= ps_est <= max_ps))

            if buy_rules.get("use_roa"):
                min_roa = float(buy_rules.get("min_roa") if buy_rules.get("min_roa") is not None else -50.0)
                max_roa = float(buy_rules.get("max_roa") if buy_rules.get("max_roa") is not None else 50.0)
                roa_est = _historical_fundamental(df, i, "roa")
                active_buy_flags.append(bool(min_roa <= roa_est <= max_roa))

            if buy_rules.get("use_roe"):
                min_roe = float(buy_rules.get("min_roe") if buy_rules.get("min_roe") is not None else -50.0)
                max_roe = float(buy_rules.get("max_roe") if buy_rules.get("max_roe") is not None else 60.0)
                roe_est = _historical_fundamental(df, i, "roe")
                active_buy_flags.append(bool(min_roe <= roe_est <= max_roe))

            if buy_rules.get("use_eps"):
                min_eps = float(buy_rules.get("min_eps") if buy_rules.get("min_eps") is not None else -10000.0)
                max_eps = float(buy_rules.get("max_eps") if buy_rules.get("max_eps") is not None else 50000.0)
                eps_est = _historical_fundamental(df, i, "eps")
                active_buy_flags.append(bool(min_eps <= eps_est <= max_eps))

            if buy_rules.get("growth_eps"):
                min_geps = float(buy_rules.get("min_growth_eps") if buy_rules.get("min_growth_eps") is not None else -500.0)
                max_geps = float(buy_rules.get("max_growth_eps") if buy_rules.get("max_growth_eps") is not None else 500.0)
                geps_est = _historical_fundamental(df, i, "growth_eps")
                active_buy_flags.append(bool(min_geps <= geps_est <= max_geps))

            if buy_rules.get("growth_rev_latest"):
                min_gr = float(buy_rules.get("min_growth_rev_latest") if buy_rules.get("min_growth_rev_latest") is not None else -200.0)
                max_gr = float(buy_rules.get("max_growth_rev_latest") if buy_rules.get("max_growth_rev_latest") is not None else 500.0)
                gr_est = _historical_fundamental(df, i, "rev_growth")
                active_buy_flags.append(bool(min_gr <= gr_est <= max_gr))

            if buy_rules.get("growth_np_latest"):
                min_np = float(buy_rules.get("min_growth_np_latest") if buy_rules.get("min_growth_np_latest") is not None else -500.0)
                max_np = float(buy_rules.get("max_growth_np_latest") if buy_rules.get("max_growth_np_latest") is not None else 1000.0)
                np_est = _historical_fundamental(df, i, "np_growth")
                active_buy_flags.append(bool(min_np <= np_est <= max_np))

            if buy_rules.get("growth_rev_prev"):
                min_grp = float(buy_rules.get("min_growth_rev_prev") if buy_rules.get("min_growth_rev_prev") is not None else -200.0)
                max_grp = float(buy_rules.get("max_growth_rev_prev") if buy_rules.get("max_growth_rev_prev") is not None else 500.0)
                grp_est = _historical_fundamental(df, i, "growth_rev_prev")
                active_buy_flags.append(bool(min_grp <= grp_est <= max_grp))

            if buy_rules.get("growth_np_prev"):
                min_npp = float(buy_rules.get("min_growth_np_prev") if buy_rules.get("min_growth_np_prev") is not None else -500.0)
                max_npp = float(buy_rules.get("max_growth_np_prev") if buy_rules.get("max_growth_np_prev") is not None else 1000.0)
                npp_est = _historical_fundamental(df, i, "growth_np_prev")
                active_buy_flags.append(bool(min_npp <= npp_est <= max_npp))

            if buy_rules.get("growth_rev_ttm"):
                min_grt = float(buy_rules.get("min_growth_rev_ttm") if buy_rules.get("min_growth_rev_ttm") is not None else -200.0)
                max_grt = float(buy_rules.get("max_growth_rev_ttm") if buy_rules.get("max_growth_rev_ttm") is not None else 500.0)
                grt_est = _historical_fundamental(df, i, "growth_rev_ttm")
                active_buy_flags.append(bool(min_grt <= grt_est <= max_grt))

            if buy_rules.get("growth_np_ttm"):
                min_npt = float(buy_rules.get("min_growth_np_ttm") if buy_rules.get("min_growth_np_ttm") is not None else -500.0)
                max_npt = float(buy_rules.get("max_growth_np_ttm") if buy_rules.get("max_growth_np_ttm") is not None else 1000.0)
                npt_est = _historical_fundamental(df, i, "growth_np_ttm")
                active_buy_flags.append(bool(min_npt <= npt_est <= max_npt))

            # Khối ngoại & Tự doanh
            if buy_rules.get("foreign_net_val") or buy_rules.get("foreign_net_buy") or buy_rules.get("foreign_net_buy_val"):
                min_fv = float(
                    buy_rules.get("min_foreign_buy_val")
                    if buy_rules.get("min_foreign_buy_val") is not None
                    else (buy_rules.get("min_foreign_val") if buy_rules.get("min_foreign_val") is not None else 0.0)
                )
                max_fv = float(
                    buy_rules.get("max_foreign_buy_val")
                    if buy_rules.get("max_foreign_buy_val") is not None
                    else (buy_rules.get("max_foreign_val") if buy_rules.get("max_foreign_val") is not None else 20000.0)
                )
                f_val_est = _get_foreign_buy_val(df, i, symbol_meta)
                active_buy_flags.append(bool(min_fv <= f_val_est <= max_fv))

            if buy_rules.get("foreign_net_vol") or buy_rules.get("foreign_net_buy_vol"):
                min_fvol = float(
                    buy_rules.get("min_foreign_buy_vol")
                    if buy_rules.get("min_foreign_buy_vol") is not None
                    else (buy_rules.get("min_foreign_vol") if buy_rules.get("min_foreign_vol") is not None else 0.0)
                )
                max_fvol = float(
                    buy_rules.get("max_foreign_buy_vol")
                    if buy_rules.get("max_foreign_buy_vol") is not None
                    else (buy_rules.get("max_foreign_val") if buy_rules.get("max_foreign_val") is not None else 500.0)
                )
                f_vol_est = _get_foreign_buy_vol(df, i, symbol_meta)
                active_buy_flags.append(bool(min_fvol <= f_vol_est <= max_fvol))

            if buy_rules.get("prop_net_val") or buy_rules.get("prop_net_buy") or buy_rules.get("prop_net_buy_val"):
                min_pv = float(
                    buy_rules.get("min_prop_buy_val")
                    if buy_rules.get("min_prop_buy_val") is not None
                    else (buy_rules.get("min_prop_val") if buy_rules.get("min_prop_val") is not None else 0.0)
                )
                max_pv = float(
                    buy_rules.get("max_prop_buy_val")
                    if buy_rules.get("max_prop_buy_val") is not None
                    else (buy_rules.get("max_prop_val") if buy_rules.get("max_prop_val") is not None else 60000.0)
                )
                p_val_est = _get_prop_buy_val(df, i, symbol_meta)
                active_buy_flags.append(bool(min_pv <= p_val_est <= max_pv))

            if buy_rules.get("prop_net_vol") or buy_rules.get("prop_net_buy_vol"):
                min_pvol = float(
                    buy_rules.get("min_prop_buy_vol")
                    if buy_rules.get("min_prop_buy_vol") is not None
                    else (buy_rules.get("min_prop_vol") if buy_rules.get("min_prop_vol") is not None else 0.0)
                )
                max_pvol = float(
                    buy_rules.get("max_prop_buy_vol")
                    if buy_rules.get("max_prop_buy_vol") is not None
                    else (buy_rules.get("max_prop_vol") if buy_rules.get("max_prop_vol") is not None else 100.0)
                )
                p_vol_est = _get_prop_buy_vol(df, i, symbol_meta)
                active_buy_flags.append(bool(min_pvol <= p_vol_est <= max_pvol))

            if active_buy_flags:
                if buy_logic == "OR":
                    tech_buy = any(active_buy_flags)
                else:
                    tech_buy = all(active_buy_flags)
            else:
                tech_buy = False

            if ai_signals is not None and len(ai_signals) == n_bars:
                ai_buy = bool(ai_signals[i] == 2)
                buy_cond = (tech_buy or ai_buy) if buy_logic == "OR" else (tech_buy and ai_buy)
            else:
                buy_cond = tech_buy
        elif ai_signals is not None and len(ai_signals) == n_bars:
            buy_cond = bool(ai_signals[i] == 2)
        else:
            # Quy tắc xu hướng mặc định: Golden Cross hoặc RSI quá bán hồi phục
            buy_cond = bool((df["SMA20"].iloc[i] > df["SMA50"].iloc[i]) and (df["RSI"].iloc[i] > 40.0))

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
                    if col in df:
                        return float(df[col].iloc[idx])
                    raise ValueError(f"Unsupported sell MA indicator column: {col}")

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
                    raise ValueError(f"Unsupported sell MA operator: {op}")

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
                        if col in df:
                            return float(df[col].iloc[idx])
                        raise ValueError(f"Unsupported sell cross target column: {col}")
                    col = f"SMA{digits}" if digits else "SMA10"
                    if col in df:
                        return float(df[col].iloc[idx])
                    raise ValueError(f"Unsupported sell cross target column: {col}")

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
                    raise ValueError(f"Unsupported sell price_cross_operator: {op}")

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
                    f_val_est = _get_foreign_sell_val(df, i, symbol_meta)
                    active_sell_flags.append(bool(min_fv <= f_val_est <= max_fv))

            # 5. KLGD tự doanh bán ròng (triệu cp)
            if sell_rules.get("prop_net_sell_vol"):
                min_pvol = float(sell_rules.get("min_prop_sell_vol") if sell_rules.get("min_prop_sell_vol") is not None else 0.0)
                max_pvol = float(sell_rules.get("max_prop_sell_vol") if sell_rules.get("max_prop_sell_vol") is not None else 50.0)
                if not (min_pvol <= 0.0 and max_pvol >= 50.0):
                    p_vol_est = _get_prop_sell_vol(df, i, symbol_meta)
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
                    if col in df:
                        return float(df[col].iloc[idx])
                    raise ValueError(f"Unsupported sell EMA indicator column: {col}")

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
                    raise ValueError(f"Unsupported sell EMA operator: {op}")

            # 8. KLGD nước ngoài bán ròng (triệu cp)
            if sell_rules.get("foreign_net_sell_vol"):
                min_fvol = float(sell_rules.get("min_foreign_sell_vol") if sell_rules.get("min_foreign_sell_vol") is not None else 0.0)
                max_fvol = float(sell_rules.get("max_foreign_sell_vol") if sell_rules.get("max_foreign_sell_vol") is not None else 300.0)
                if not (min_fvol <= 0.0 and max_fvol >= 300.0):
                    f_vol_est = _get_foreign_sell_vol(df, i, symbol_meta)
                    active_sell_flags.append(bool(min_fvol <= f_vol_est <= max_fvol))

            # 9. RS
            if sell_rules.get("use_rs"):
                if "RS" not in df:
                    raise ValueError("Historical RS indicator is required.")
                min_rs = float(sell_rules.get("min_rs") if sell_rules.get("min_rs") is not None else 0.0)
                max_rs = float(sell_rules.get("max_rs") if sell_rules.get("max_rs") is not None else 100.0)
                if not (min_rs <= 0.0 and max_rs >= 99.9):
                    rs_val = float(df["RS"].iloc[i])
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
                    raise ValueError(f"Unsupported sell MACD operator: {op}")

            # 11. GTGD tự doanh bán ròng (Tỷ)
            if sell_rules.get("prop_net_sell_val"):
                min_pv = float(sell_rules.get("min_prop_sell_val") if sell_rules.get("min_prop_sell_val") is not None else 0.0)
                max_pv = float(sell_rules.get("max_prop_sell_val") if sell_rules.get("max_prop_sell_val") is not None else 48633.0)
                if not (min_pv <= 0.0 and max_pv >= 48633.0):
                    p_val_est = _get_prop_sell_val(df, i, symbol_meta)
                    active_sell_flags.append(bool(min_pv <= p_val_est <= max_pv))

            # 12. Bollinger Bands
            if sell_rules.get("use_bb"):
                active_sell_flags.append(bool(df["Close"].iloc[i] >= df["BB_Upper"].iloc[i]))

            if active_sell_flags:
                if sell_logic == "AND":
                    tech_sell = all(active_sell_flags)
                else:
                    tech_sell = any(active_sell_flags)
            else:
                tech_sell = False

            if ai_signals is not None and len(ai_signals) == n_bars:
                ai_sell = bool(ai_signals[i] == 0)
                sell_cond = (tech_sell and ai_sell) if sell_logic == "AND" else (tech_sell or ai_sell)
            else:
                sell_cond = tech_sell
        elif ai_signals is not None and len(ai_signals) == n_bars:
            sell_cond = bool(ai_signals[i] == 0)
        elif not has_custom_buy:
            sell_cond = bool((df["SMA20"].iloc[i] < df["SMA50"].iloc[i]) or (df["RSI"].iloc[i] > 70.0))
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
    price_unit: str = "kVND",
) -> dict[str, Any]:
    """
    Thực thi mô phỏng Backtesting cho danh mục đa mã (Rổ chỉ số, Ngành, hoặc Danh mục tự chọn)
    trong dải ngày xác định (tối đa 1 năm theo chuẩn DNSE), chia đều vốn (Equal-Weight).
    """
    from vn_stock.data_ingestion import load_local_data
    from vn_stock.features import ALL_FEATURE_COLS

    clean_symbols = list(dict.fromkeys(s.strip().upper() for s in symbols if s.strip()))
    if not clean_symbols:
        raise ValueError("A nonempty explicit symbol universe is required.")

    if model_type.lower() not in ("none", "lightgbm", "lgb", "lstm"):
        raise ValueError(f"Unsupported model type: {model_type}")

    # Đảm bảo dải ngày hợp lệ
    end_dt = pd.to_datetime(end_date) if end_date else pd.to_datetime("today")
    start_dt = pd.to_datetime(start_date) if start_date else (end_dt - pd.Timedelta(days=365))

    n_symbols = len(clean_symbols)
    sub_capital = float(initial_capital) / n_symbols

    # Tải mô hình AI nếu có sẵn (hỗ trợ cả LightGBM và PyTorch LSTM)
    booster = None
    lstm_model = None
    scaler = None
    model_info: dict[str, Any] = {}
    data_fingerprints: dict[str, str] = {}
    signal_fingerprints: dict[str, str] = {}
    m_clean = model_type.lower()
    if m_clean in ("lightgbm", "lgb", "lstm"):
        try:
            from vn_stock.modeling.predict import load_prediction_snapshot

            loaded_model, scaler, model_info = load_prediction_snapshot(
                model_type="lightgbm" if m_clean in ("lightgbm", "lgb") else "lstm",
                models_dir=MODELS_DIR,
                horizon=3,
            )
            if m_clean in ("lightgbm", "lgb"):
                booster = loaded_model
            else:
                lstm_model = loaded_model
        except Exception as e:
            raise ValueError(f"Requested AI model is unavailable: {model_type}") from e

    individual_results: dict[str, Any] = {}
    breakdown_list: list[dict[str, Any]] = []
    equity_dfs: list[pd.DataFrame] = []

    for sym in clean_symbols:
        try:
            df_sym = load_local_data(sym)
            if df_sym is None or df_sym.empty:
                raise ValueError(f"Missing local market data for {sym}; refresh data separately.")

            df_sym = df_sym.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_sym["Date"]):
                df_sym["Date"] = pd.to_datetime(df_sym["Date"])

            mask = (df_sym["Date"] >= start_dt) & (df_sym["Date"] <= end_dt)
            filtered_df = df_sym[mask].copy().sort_values("Date").reset_index(drop=True)

            if len(filtered_df) < 5:
                raise ValueError(f"Insufficient market observations for {sym} in requested interval.")

            historical_df = df_sym[df_sym["Date"] <= end_dt].sort_values("Date").reset_index(drop=True)
            data_fingerprints[sym] = _data_fingerprint(historical_df)
            prepared_history = prepare_backtest_df(historical_df)
            df_prepared = prepared_history[prepared_history["Date"] >= start_dt].reset_index(drop=True)

            ai_signals = None
            if (booster is not None or lstm_model is not None) and scaler is not None:
                try:
                    from vn_stock.data_ingestion import fetch_daily_index
                    from vn_stock.features import compute_features_per_symbol

                    df_for_feat = df_sym.copy()
                    if "VNINDEX_Return_1d" not in df_for_feat.columns:
                        vni_idx = fetch_daily_index("VNINDEX")
                        df_for_feat = pd.merge(
                            df_for_feat, vni_idx[["Date", "VNINDEX_Return_1d"]], on="Date", how="left"
                        )
                    computed_feats = compute_features_per_symbol(df_for_feat, drop_na=False)
                    mask_dates = computed_feats["Date"].isin(filtered_df["Date"])
                    aligned_feats = computed_feats[mask_dates].copy().sort_values("Date").reset_index(drop=True)

                    if len(aligned_feats) == len(df_prepared):
                        feat_scaled = aligned_feats.copy()
                        from vn_stock.config import SYMBOL_TO_CODE

                        feat_scaled["Symbol_Code"] = SYMBOL_TO_CODE.get(sym, 0)
                        feat_scaled["Symbol"] = sym
                        from vn_stock.features import transform_model_features
                        feat_scaled = transform_model_features(feat_scaled, scaler)

                        if booster is not None:
                            probs = booster.predict(feat_scaled[ALL_FEATURE_COLS])
                            ai_signals = np.argmax(probs, axis=1)
                        elif lstm_model is not None:
                            import torch

                            from vn_stock.features import create_multivariate_sequences

                            pre_mask = computed_feats["Date"] < filtered_df["Date"].iloc[0]
                            sequence_length = int(model_info.get("seq_length", 20))
                            warm_feats = computed_feats[pre_mask].sort_values("Date").tail(sequence_length - 1).copy()
                            if len(warm_feats) < sequence_length - 1:
                                raise ValueError(f"Insufficient causal LSTM warm-up for {sym}.")
                            warm_scaled = warm_feats.copy()
                            warm_scaled["Symbol_Code"] = SYMBOL_TO_CODE.get(sym, 0)
                            warm_scaled["Symbol"] = sym
                            warm_scaled = transform_model_features(warm_scaled, scaler)

                            xs, _ = create_multivariate_sequences(
                                feat_scaled,
                                warmup_df=warm_scaled,
                                feature_cols=ALL_FEATURE_COLS,
                                seq_length=sequence_length,
                            )
                            if len(xs) == len(df_prepared):
                                lstm_model.eval()
                                with torch.no_grad():
                                    device = next(lstm_model.parameters()).device
                                    xt = torch.from_numpy(xs).to(device)
                                    probs = lstm_model.predict_proba(xt).cpu().numpy()
                                    ai_signals = np.argmax(probs, axis=1)
                except Exception as pred_err:
                    raise ValueError(f"AI preprocessing failed for {sym}: {pred_err}") from pred_err

            if m_clean != "none" and ai_signals is None:
                raise ValueError(f"AI inference did not produce aligned signals for {sym}.")

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

            signal_fingerprints[sym] = _data_fingerprint(pd.DataFrame({"signal": signals}))
            metrics, eq_df, trades_df = simulate_vietnam_trading(
                df=trading_prices_vnd(df_prepared, price_unit),
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
                    "sharpe": _round_metric(metrics.sharpe_ratio, 4),
                    "sortino": _round_metric(metrics.sortino_ratio, 4),
                    "mdd_pct": round(metrics.max_drawdown_pct, 2),
                    "win_rate_pct": _round_metric(metrics.win_rate_pct, 2),
                    "profit_factor": _round_metric(metrics.profit_factor, 4),
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

            sym_equity_curve = []
            for r in eq_df[
                ["Date", "Total_Equity", "Benchmark_Equity", "Drawdown_Pct", "Daily_Return"]
            ].to_dict(orient="records"):
                sym_equity_curve.append(
                    {
                        "date": str(r["Date"]),
                        "total_equity": round(float(r["Total_Equity"]), 2),
                        "benchmark_equity": round(float(r["Benchmark_Equity"]), 2),
                        "drawdown_pct": round(float(r["Drawdown_Pct"]), 2),
                        "daily_return": round(float(r["Daily_Return"]), 2),
                    }
                )

            individual_results[sym] = {
                "metrics": metrics.__dict__,
                "equity_curve": sym_equity_curve,
                "trades": trades_list,
            }
        except Exception as sym_err:
            raise ValueError(f"Backtest failed for {sym}: {sym_err}") from sym_err

    if not equity_dfs:
        raise ValueError("Không có dữ liệu hợp lệ cho danh sách mã đã chọn trong dải ngày.")

    # Tổng hợp Portfolio Equity Curve
    merged_eq = equity_dfs[0]
    for other_eq in equity_dfs[1:]:
        merged_eq = pd.merge(merged_eq, other_eq, on="Date", how="outer")

    merged_eq = merged_eq.sort_values("Date").reset_index(drop=True)
    merged_eq = merged_eq.ffill().fillna(sub_capital)
    # A missing symbol remains in cash, rather than losing its allocated capital.
    for missing_sym in set(clean_symbols) - set(individual_results):
        merged_eq[f"Equity_{missing_sym}"] = sub_capital
        merged_eq[f"BH_{missing_sym}"] = sub_capital

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

    # Use the same unrounded equity returns and actual trade cash flows as single-symbol runs.
    all_trades = [TradeRecord(**trade) for result in individual_results.values()
                  for trade in result["trades"]]
    benchmark_return = (merged_eq["Benchmark_Equity"].iloc[-1] / initial_capital - 1) * 100
    metrics = calculate_financial_metrics(
        merged_eq["Total_Equity"], initial_capital, all_trades,
        buy_and_hold_return_pct=float(benchmark_return),
    )
    aggregate_metrics = metrics.__dict__.copy()
    aggregate_metrics.pop("equity_curve")
    aggregate_metrics["max_gain_pct"] = metrics.best_trade_return_pct
    aggregate_metrics["max_loss_pct"] = metrics.worst_trade_return_pct
    wins = [float(t.realized_return_pct) for t in all_trades
            if t.order_type == "SELL" and t.realized_pnl is not None and t.realized_pnl > 0 and t.realized_return_pct is not None]
    losses = [float(t.realized_return_pct) for t in all_trades
              if t.order_type == "SELL" and t.realized_pnl is not None and t.realized_pnl < 0 and t.realized_return_pct is not None]
    avg_loss = abs(float(np.mean(losses))) if losses else 0.0
    aggregate_metrics["reward_risk_ratio"] = (
        round(float(np.mean(wins)) / avg_loss, 2) if wins and losses and avg_loss > 1e-9 else None
    )

    return {
        "config": {
            "engine_contract": "daily_cash_settlement_v2",
            "symbols": clean_symbols, "universe_kind": "requested_snapshot_not_historical_constituents",
            "start_date": str(start_dt.date()), "end_date": str(end_dt.date()),
            "initial_capital": initial_capital, "allocation": "equal_weight_segregated_cash",
            "model_type": m_clean, "model_info": model_info,
            "training_provenance": _load_training_provenance(MODELS_DIR) if m_clean != "none" else {},
            "evaluation_kind": "rule_based_historical_simulation" if m_clean == "none" else "production_model_historical_simulation",
            "independent_oos": False,
            "leakage_warning": (
                None if m_clean == "none"
                else "Production artifact may overlap the simulated historical window; not independent OOS."
            ),
            "buy_rules": buy_rules or {}, "sell_rules": sell_rules or {},
            "slippage_rate": slippage_rate, "fee_rate": fee_rate, "tax_rate": tax_rate,
            "lot_size": lot_size, "settlement_delay": settlement_delay,
            "execution_price": "open", "close_at_end": True,
            "cash_settlement": "no_advance_afternoon_T_plus_delay", "risk_execution": "standing_open_checks",
            "settlement_regime_effective_from": "2022-08-29",
            "settlement_regime_warning": (
                "Simulation includes dates before 2022-08-29 when afternoon T+2 settlement was not yet effective."
                if str(start_dt.date()) < "2022-08-29"
                else None
            ),
            "price_adjustment_status": "unverified",
            "corporate_actions_modeled": False,
            "dividend_modeled": False,
            "take_profit_pct": take_profit_pct, "stop_loss_pct": stop_loss_pct,
            "trailing_stop_pct": trailing_stop_pct, "input_price_unit": price_unit, "price_unit": "VND",
            "data_fingerprints": data_fingerprints, "signal_fingerprints": signal_fingerprints,
            "pandas_version": pd.__version__,
            "benchmark": "same_symbol_equal_weight_buy_and_hold_price_return_after_costs",
        },
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
        "--scope",
        type=str,
        default="VN30",
        choices=["VN30", "CORE"],
        help="Phạm vi danh mục kiểm thử: 'VN30' (toàn bộ 30 mã) hoặc 'CORE' (5 mã cốt lõi).",
    )
    parser.add_argument(
        "--all-symbols",
        action="store_true",
        help="Chạy đồng loạt trên toàn bộ danh mục (--scope, mặc định VN30).",
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
        print(f"BẢNG TỔNG HỢP KIỂM THỬ BACKTEST T+2 TRÊN TẬP OOS ({args.model.upper()} - {args.scope})")
        print("=" * 80)
        summary_df = backtest_all_symbols(
            symbols=args.scope,
            model_type=args.model,
            initial_capital=args.capital,
        )
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
        print(f"Tỷ số Sharpe năm hóa:   {_display_metric(m.sharpe_ratio, 4)}")
        print(f"Tỷ số Sortino năm hóa:  {_display_metric(m.sortino_ratio, 4)}")
        print(f"Độ sụt giảm tối đa MDD: {m.max_drawdown_pct:.2f}%")
        print(f"Tỷ số Calmar:           {_display_metric(m.calmar_ratio, 4)}")
        print(f"VaR 95% / CVaR 95%:     {_display_metric(m.var_95_pct, 2)}% / {_display_metric(m.cvar_95_pct, 2)}%")
        print(
            f"Tỷ lệ thắng (Win Rate): {_display_metric(m.win_rate_pct, 2)}% ({m.winning_trades}/{m.total_trades} lệnh)"
        )
        print(f"Hệ số Profit Factor:    {_display_metric(m.profit_factor, 4)}")
        print(f"Thời gian giữ TB:       {_display_metric(m.avg_holding_days, 1)} phiên")
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
                f"Sharpe ngẫu nhiên: Mean={_display_metric(mc_res['sharpe_stats']['mean'], 4)}, 90% CI=[{_display_metric(mc_res['sharpe_stats']['p5'], 4)}, {_display_metric(mc_res['sharpe_stats']['p95'], 4)}]"
            )
            if "ai_comparison" in mc_res:
                comp = mc_res["ai_comparison"]
                print(
                    f"P-value Sharpe:    {_display_metric(comp['p_value_sharpe'], 4)} (Ý nghĩa thống kê: {comp['statistically_significant_at_5pct']})"
                )
                print(f"P-value ROI:       {comp['p_value_roi']:.4f}")
            print("=" * 65)


def get_strategy_presets() -> list[dict[str, Any]]:
    """
    Cung cấp danh mục 8 mẫu chiến lược khởi tạo chạy hoàn toàn trên dữ liệu OHLCV lịch sử.
    Tích hợp sẵn bộ điều kiện chỉ báo kỹ thuật/thanh khoản và quy tắc quản trị rủi ro (Take Profit, Stop Loss, Trailing Stop).
    """
    return [
        {
            "id": "preset_ema20_breakout",
            "name": "Thuận xu hướng (Break out EMA 20)",
            "category": "Trend Following",
            "description": "Săn tìm điểm bứt phá mạnh mẽ khi giá cắt lên EMA20 kèm khối lượng đột biến phiên mua vượt ít nhất 50% và thanh khoản bình quân 10 phiên đạt tối thiểu 10 tỷ đồng.",
            "target_symbols": ["SSI", "STB", "VPB", "HPG"],
            "default_symbol": "HPG",
            "conditions_summary": "Giá cắt lên EMA 20 • %KLGD đột biến ≥ 50% • GTGD 10 phiên ≥ 10 tỷ",
            "win_rate_pct": None,
            "cumulative_pnl_pct": None,
            "risk_reward_ratio": None,
            "copy_count": None,
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
            "win_rate_pct": None,
            "cumulative_pnl_pct": None,
            "risk_reward_ratio": None,
            "copy_count": None,
            "take_profit_pct": 0.20,
            "stop_loss_pct": 0.07,
            "trailing_stop_pct": 0.05,
            "model_type": "lightgbm",
            "timeframe": "1 ngày (Daily)",
        },
        {
            "id": "preset_fair_val_flow",
            "name": "Xác nhận xu hướng MACD & Động lượng giá",
            "category": "Trend & Momentum",
            "description": "Kết hợp tín hiệu MACD cắt lên đường tín hiệu, giá mở cửa phiên nay cao hơn phiên trước và bộ lọc RSI(14) vùng tích cực 45-70.",
            "target_symbols": ["VN30", "VNM", "VCB", "ACB"],
            "default_symbol": "VNM",
            "conditions_summary": "MACD cắt lên tín hiệu • Giá mở cửa T0 > T-1 • RSI(14) 45 - 70",
            "win_rate_pct": None,
            "cumulative_pnl_pct": None,
            "risk_reward_ratio": None,
            "copy_count": None,
            "take_profit_pct": 0.20,
            "stop_loss_pct": 0.07,
            "trailing_stop_pct": 0.0,
            "model_type": "lightgbm",
            "timeframe": "1 ngày (Daily)",
        },
        {
            "id": "preset_semi_canslim",
            "name": "Cổ phiếu dẫn dắt động lượng & Thanh khoản (RS)",
            "category": "Relative Strength",
            "description": "Lọc các cổ phiếu dẫn dắt trong VN30 có sức mạnh giá tương đối RS ≥ 70, giá nằm trên SMA 50, thanh khoản 10 phiên ≥ 10 tỷ và RSI(14) vùng 50-80.",
            "target_symbols": ["VN30", "FPT", "MWG", "TCB"],
            "default_symbol": "MWG",
            "conditions_summary": "Sức mạnh giá RS ≥ 70 • Giá nằm trên MA 50 • GTGD 10 phiên ≥ 10 tỷ • RSI(14) 50 - 80",
            "win_rate_pct": None,
            "cumulative_pnl_pct": None,
            "risk_reward_ratio": None,
            "copy_count": None,
            "take_profit_pct": 0.20,
            "stop_loss_pct": 0.07,
            "trailing_stop_pct": 0.05,
            "model_type": "lstm",
            "timeframe": "1 ngày (Daily)",
        },
        {
            "id": "preset_cheap_bank",
            "name": "Nhóm Ngân hàng hồi phục kỹ thuật & GTGD 10 tỷ",
            "category": "Sector Rotation",
            "description": "Chiến lược giao dịch nhóm cổ phiếu Ngân hàng khi giá cắt lên EMA 20 từ vùng tích lũy RSI(14) 35-65 kèm thanh khoản bình quân 10 phiên ≥ 10 tỷ đồng.",
            "target_symbols": ["SHB", "MBB", "VCB", "VPB", "TCB", "STB"],
            "default_symbol": "MBB",
            "conditions_summary": "Giá cắt lên EMA 20 • RSI(14) 35 - 65 • GTGD 10 phiên ≥ 10 tỷ • Nhóm Ngân hàng",
            "win_rate_pct": None,
            "cumulative_pnl_pct": None,
            "risk_reward_ratio": None,
            "copy_count": None,
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
            "target_symbols": ["VN30", "HPG", "SSI", "STB"],
            "default_symbol": "HPG",
            "conditions_summary": "%KLGD đột biến 10 phiên ≥ 30% • Giá mở cửa T0 > Giá mở cửa T-1",
            "win_rate_pct": None,
            "cumulative_pnl_pct": None,
            "risk_reward_ratio": None,
            "copy_count": None,
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
            "win_rate_pct": None,
            "cumulative_pnl_pct": None,
            "risk_reward_ratio": None,
            "copy_count": None,
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
            "win_rate_pct": None,
            "cumulative_pnl_pct": None,
            "risk_reward_ratio": None,
            "copy_count": None,
            "take_profit_pct": 0.20,
            "stop_loss_pct": 0.15,
            "trailing_stop_pct": 0.07,
            "model_type": "lstm",
            "timeframe": "1 ngày (Daily)",
        },
    ]


def get_recent_strategy_signals() -> list[dict[str, Any]]:
    """No persisted, timestamped signal feed is wired here yet; never invent live signals."""
    return []
