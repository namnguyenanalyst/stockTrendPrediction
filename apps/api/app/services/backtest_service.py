"""Service thực thi mô phỏng kiểm thử chiến lược đầu tư (Backtest Simulator) cho API."""

import logging
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import pandas as pd
from app.core.config import settings
from app.models.schemas import (
    BacktestMetricsSchema,
    BacktestRequest,
    BacktestResponse,
    BacktestSummaryItem,
    BacktestSummaryResponse,
    EquityCurvePoint,
    TradeLogItem,
)
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Đảm bảo đường dẫn apps/ml nằm trong sys.path
if str(settings.ML_APP_DIR) not in sys.path:
    sys.path.insert(0, str(settings.ML_APP_DIR))


def run_backtest_simulation(req: BacktestRequest) -> BacktestResponse:
    """
    Thực hiện chạy kiểm thử chiến lược đầu tư theo tham số yêu cầu của người dùng.

    Mô phỏng tuân thủ nghiêm ngặt quy chế thị trường chứng khoán Việt Nam:
    - Khớp lệnh T+2, giá Open_{t+1} kèm trượt giá (Slippage)
    - Khấu trừ phí môi giới và thuế chuyển nhượng thực tế
    - Khớp lệnh theo lô chẵn 100 cổ phiếu
    """
    clean_sym = req.symbol.upper()
    model_clean = req.model_type.lower()

    if model_clean not in ["lightgbm", "lstm"]:
        raise HTTPException(
            status_code=400,
            detail=f"Mô hình '{req.model_type}' không hợp lệ. Chỉ hỗ trợ 'lightgbm' hoặc 'lstm'.",
        )

    # Tự động đảm bảo nến lịch sử có sẵn cho mã kiểm thử
    from vn_stock.data_ingestion import fetch_stock_data, load_local_data
    if load_local_data(clean_sym) is None:
        try:
            fetch_stock_data(clean_sym)
        except Exception as exc:
            raise HTTPException(
                status_code=404,
                detail=f"Không tìm thấy dữ liệu cho mã '{clean_sym}': {exc}",
            )


    try:
        from vn_stock.backtest import backtest_symbol_oos

        res = backtest_symbol_oos(
            symbol=clean_sym,
            model_type=model_clean,
            models_dir=settings.MODELS_DIR,
            initial_capital=req.initial_capital,
            slippage_rate=req.slippage_rate,
        )

        m = res.metrics
        metrics_schema = BacktestMetricsSchema(
            initial_capital=m.initial_capital,
            final_equity=m.final_equity,
            total_return_pct=m.total_return_pct,
            cagr_pct=m.cagr_pct,
            buy_and_hold_return_pct=m.buy_and_hold_return_pct,
            excess_return_pct=m.excess_return_pct,
            annualized_volatility_pct=m.annualized_volatility_pct,
            sharpe_ratio=m.sharpe_ratio,
            sortino_ratio=m.sortino_ratio,
            max_drawdown_pct=m.max_drawdown_pct,
            calmar_ratio=m.calmar_ratio,
            var_95_pct=m.var_95_pct,
            cvar_95_pct=m.cvar_95_pct,
            win_rate_pct=m.win_rate_pct,
            profit_factor=m.profit_factor,
            total_trades=m.total_trades,
            winning_trades=m.winning_trades,
            losing_trades=m.losing_trades,
            avg_trade_return_pct=m.avg_trade_return_pct,
            avg_holding_days=m.avg_holding_days,
            total_fees_paid=m.total_fees_paid,
            total_taxes_paid=m.total_taxes_paid,
            total_costs=m.total_costs,
            cost_impact_pct=m.cost_impact_pct,
        )

        # Chuyển đổi đường cong tài sản
        equity_curve_points = []
        for _, row in res.equity_df.iterrows():
            d_str = (
                row["Date"].strftime("%Y-%m-%d")
                if hasattr(row["Date"], "strftime")
                else str(row["Date"])[:10]
            )
            equity_curve_points.append(
                EquityCurvePoint(
                    date=d_str,
                    total_equity=round(float(row["Total_Equity"]), 2),
                    benchmark_equity=round(
                        float(row.get("Benchmark_Equity", req.initial_capital)), 2
                    ),
                    drawdown_pct=round(float(row.get("Drawdown_Pct", 0.0)), 2),
                    daily_return=round(float(row.get("Daily_Return", 0.0)), 2),
                )
            )

        # Chuyển đổi nhật ký giao dịch
        trade_items = []
        if not res.trades_df.empty:
            for _, tr in res.trades_df.iterrows():
                trade_items.append(
                    TradeLogItem(
                        trade_id=int(tr["trade_id"]),
                        order_type=str(tr["order_type"]),
                        exec_date=str(tr["exec_date"]),
                        exec_price=round(float(tr["exec_price"]), 2),
                        shares=int(tr["shares"]),
                        fee=round(float(tr["fee"]), 2),
                        tax=round(float(tr["tax"]), 2),
                        net_cash_flow=round(float(tr["net_cash_flow"]), 2),
                        realized_pnl=round(float(tr["realized_pnl"]), 2)
                        if tr["realized_pnl"] is not None and not pd.isna(tr["realized_pnl"])
                        else None,
                        realized_return_pct=round(float(tr["realized_return_pct"]), 2)
                        if tr["realized_return_pct"] is not None
                        and not pd.isna(tr["realized_return_pct"])
                        else None,
                        holding_days=round(float(tr["holding_days"]), 1)
                        if tr["holding_days"] is not None and not pd.isna(tr["holding_days"])
                        else None,
                        reason=str(tr.get("reason", "")),
                    )
                )

        return BacktestResponse(
            symbol=clean_sym,
            strategy_name=res.strategy_name,
            config=res.config,
            metrics=metrics_schema,
            equity_curve=equity_curve_points,
            trades=trade_items,
        )
    except Exception as err:
        logger.exception("Lỗi thực thi Backtest cho %s", clean_sym)
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi thực thi Backtest: {err!s}",
        )


def get_backtest_summary(model_type: str = "lightgbm") -> BacktestSummaryResponse:
    """Lấy bảng tổng hợp kết quả Backtest Out-of-Sample trên các mã cổ phiếu."""
    model_clean = model_type.lower()
    if model_clean not in ["lightgbm", "lstm"]:
        raise HTTPException(
            status_code=400,
            detail=f"Mô hình '{model_type}' không hợp lệ. Chỉ hỗ trợ 'lightgbm' hoặc 'lstm'.",
        )

    try:
        from vn_stock.backtest import backtest_all_symbols

        df_summary = backtest_all_symbols(
            symbols=settings.CORE_SYMBOLS,
            model_type=model_clean,
        )

        items = [
            BacktestSummaryItem(
                symbol=row["Symbol"],
                model=row["Model"],
                roi_pct=round(float(row["ROI %"]), 2),
                bh_roi_pct=round(float(row["B&H ROI %"]), 2),
                excess_pct=round(float(row["Excess %"]), 2),
                sharpe=round(float(row["Sharpe"]), 4),
                sortino=round(float(row["Sortino"]), 4),
                mdd_pct=round(float(row["MDD %"]), 2),
                win_rate_pct=round(float(row["Win Rate %"]), 2),
                profit_factor=round(float(row["Profit Factor"]), 4),
                trades=int(row["Trades"]),
                costs=round(float(row["Costs (VND)"]), 2),
            )
            for _, row in df_summary.iterrows()
        ]

        return BacktestSummaryResponse(
            model_type=model_clean.upper(),
            summary=items,
        )
    except Exception as err:
        logger.exception("Lỗi tổng hợp Backtest")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tổng hợp kết quả Backtest: {err!s}",
        )
