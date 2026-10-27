import logging
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import pandas as pd
from app.core.config import settings
from app.models.schemas import (
    AdvancedBacktestRequest,
    BacktestConditionFilter,
    BacktestMetricsSchema,
    BacktestRequest,
    BacktestResponse,
    BacktestScopeType,
    BacktestSummaryItem,
    BacktestSummaryResponse,
    EquityCurvePoint,
    IndividualResultItem,
    PortfolioBacktestResponse,
    RecentSignalItem,
    RecentSignalsResponse,
    StrategyPresetItem,
    StrategyPresetsResponse,
    SymbolBreakdownItem,
    TradeLogItem,
)
from app.services import stock_service
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
            take_profit_pct=req.take_profit_pct,
            stop_loss_pct=req.stop_loss_pct,
            trailing_stop_pct=req.trailing_stop_pct,
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


def get_backtest_summary(
    model_type: str = "lightgbm",
    symbols: list[str] | None = None,
    scope: str = "CORE",
) -> BacktestSummaryResponse:
    """Lấy bảng tổng hợp kết quả Backtest Out-of-Sample trên các mã cổ phiếu (mặc định CORE 5 mã, hoặc VN30 30 mã)."""
    model_clean = model_type.lower()
    if model_clean not in ["lightgbm", "lstm"]:
        raise HTTPException(
            status_code=400,
            detail=f"Mô hình '{model_type}' không hợp lệ. Chỉ hỗ trợ 'lightgbm' hoặc 'lstm'.",
        )

    try:
        from vn_stock.backtest import backtest_all_symbols

        if symbols is not None and len(symbols) > 0:
            target_symbols = [s.upper() for s in symbols]
        elif scope.upper() == "CORE":
            target_symbols = settings.CORE_SYMBOLS
        else:
            target_symbols = getattr(settings, "VN30_SYMBOLS", settings.CORE_SYMBOLS)

        df_summary = backtest_all_symbols(
            symbols=target_symbols,
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


def get_presets_service() -> StrategyPresetsResponse:
    """Trả về danh mục 8 chiến thuật mẫu chuẩn DNSE."""
    try:
        from vn_stock.backtest import get_strategy_presets

        raw_presets = get_strategy_presets()
        items = [StrategyPresetItem(**p) for p in raw_presets]
        return StrategyPresetsResponse(presets=items)
    except Exception as err:
        logger.exception("Lỗi lấy danh sách chiến thuật mẫu")
        raise HTTPException(
            status_code=500,
            detail=f"Không thể tải danh sách chiến thuật mẫu: {err!s}",
        )


def get_recent_signals_service() -> RecentSignalsResponse:
    """Trả về danh sách tín hiệu mới near-realtime chuẩn DNSE."""
    try:
        from vn_stock.backtest import get_recent_strategy_signals

        raw_signals = get_recent_strategy_signals()
        items = [RecentSignalItem(**s) for s in raw_signals]
        return RecentSignalsResponse(signals=items)
    except Exception as err:
        logger.exception("Lỗi lấy danh sách tín hiệu mới")
        raise HTTPException(
            status_code=500,
            detail=f"Không thể tải danh sách tín hiệu mới: {err!s}",
        )


def run_advanced_backtest(req: AdvancedBacktestRequest) -> PortfolioBacktestResponse:
    """
    Thực thi kiểm thử chiến lược đầu tư toàn diện theo chuẩn DNSE:
    - Hỗ trợ 4 phạm vi: Rổ chỉ số (VN30, VN100), Cổ phiếu đơn lẻ, Ngành nghề, Danh mục tự chọn.
    - Ràng buộc khoảng thời gian chọn không quá 1 năm (tối đa 365 ngày).
    - Áp dụng các điều kiện Mua / Bán chi tiết kết hợp quản trị rủi ro Stop Loss, Take Profit, Trailing Stop.
    """
    start_dt = pd.to_datetime(req.start_date)
    end_dt = pd.to_datetime(req.end_date)

    if start_dt > end_dt:
        raise HTTPException(
            status_code=400,
            detail="Ngày bắt đầu không được lớn hơn ngày kết thúc.",
        )

    diff_days = (end_dt - start_dt).days
    if diff_days > 365:
        raise HTTPException(
            status_code=400,
            detail="Khoảng thời gian chọn không quá 1 năm (tối đa 365 ngày).",
        )

    # 1. Phân giải danh sách mã cổ phiếu cần kiểm thử
    target_symbols: list[str] = []
    scope_target = ""

    if req.scope_type == BacktestScopeType.STOCK:
        clean_s = req.symbol.strip().upper()
        target_symbols = [clean_s]
        scope_target = clean_s
    elif req.scope_type == BacktestScopeType.INDEX:
        idx = req.index_name or "VN30"
        target_symbols = stock_service.get_index_constituents(idx)
        scope_target = f"Rổ chỉ số {idx.upper()}"
    elif req.scope_type == BacktestScopeType.SECTOR:
        sec_name = req.sector_name or "Ngân hàng"
        sectors = stock_service.get_available_sectors()
        matched = [s for s in sectors if s["sector"].lower() == sec_name.lower()]
        if matched:
            target_symbols = matched[0]["symbols"]
        else:
            target_symbols = [
                s.symbol for s in stock_service.get_available_symbols()
                if s.sector.lower() == sec_name.lower()
            ]
        if not target_symbols:
            target_symbols = ["VCB", "BID", "CTG", "TCB", "MBB"]
        scope_target = f"Ngành {sec_name}"
    elif req.scope_type == BacktestScopeType.PORTFOLIO:
        if req.portfolio_symbols and len(req.portfolio_symbols) > 0:
            target_symbols = [s.strip().upper() for s in req.portfolio_symbols if s.strip()]
        else:
            target_symbols = ["VIC", "HPG", "FPT"]
        scope_target = f"Danh mục ({len(target_symbols)} mã)"

    # 2. Chuẩn bị metadata và gọi engine
    try:
        from vn_stock.backtest import run_portfolio_backtest

        available_symbols = stock_service.get_available_symbols()
        metadata = {
            s.symbol: {"name": s.name, "sector": s.sector}
            for s in available_symbols
        }

        buy_dict = req.buy_conditions.model_dump()
        sell_dict = req.sell_conditions.model_dump()

        # Nếu không bật cài đặt nâng cao: áp dụng chuẩn DNSE (vốn 100tr, không trượt giá, không mô hình AI)
        effective_capital = req.initial_capital if req.use_advanced_settings else 100_000_000.0
        effective_slippage = req.slippage_rate if req.use_advanced_settings else 0.0
        effective_model = req.model_type if req.use_advanced_settings else "none"

        res = run_portfolio_backtest(
            symbols=target_symbols,
            start_date=req.start_date,
            end_date=req.end_date,
            initial_capital=effective_capital,
            model_type=effective_model,
            buy_rules=buy_dict,
            sell_rules=sell_dict,
            slippage_rate=effective_slippage,
            take_profit_pct=req.sell_conditions.take_profit_pct,
            stop_loss_pct=req.sell_conditions.stop_loss_pct,
            trailing_stop_pct=req.sell_conditions.trailing_stop_pct,
            symbol_metadata=metadata,
        )

        parsed_individual: dict[str, IndividualResultItem] = {}
        for sym, ind in res.get("individual_results", {}).items():
            sym_pts = [
                EquityCurvePoint(
                    date=str(pt.get("date") or pt.get("Date")),
                    total_equity=round(
                        float(pt.get("total_equity") if pt.get("total_equity") is not None else pt.get("Total_Equity", 0)), 2
                    ),
                    benchmark_equity=round(
                        float(pt.get("benchmark_equity") if pt.get("benchmark_equity") is not None else pt.get("Benchmark_Equity", 0)), 2
                    ),
                    drawdown_pct=round(
                        float(pt.get("drawdown_pct") if pt.get("drawdown_pct") is not None else pt.get("Drawdown_Pct", 0)), 2
                    ),
                    daily_return=round(
                        float(pt.get("daily_return") if pt.get("daily_return") is not None else pt.get("Daily_Return", 0)), 2
                    ),
                )
                for pt in ind.get("equity_curve", [])
            ]
            sym_trades = []
            for t in ind.get("trades", []):
                if isinstance(t, TradeLogItem):
                    sym_trades.append(t)
                elif isinstance(t, dict):
                    sym_trades.append(
                        TradeLogItem(
                            trade_id=int(t.get("trade_id", 0)),
                            order_type=str(t.get("order_type", "BUY")),
                            exec_date=str(t.get("exec_date", "")),
                            exec_price=round(float(t.get("exec_price", 0.0)), 2),
                            shares=int(t.get("shares", 0)),
                            fee=round(float(t.get("fee", 0.0)), 2),
                            tax=round(float(t.get("tax", 0.0)), 2),
                            net_cash_flow=round(float(t.get("net_cash_flow", 0.0)), 2),
                            realized_pnl=(
                                round(float(t["realized_pnl"]), 2)
                                if t.get("realized_pnl") is not None and not pd.isna(t["realized_pnl"])
                                else None
                            ),
                            realized_return_pct=(
                                round(float(t["realized_return_pct"]), 2)
                                if t.get("realized_return_pct") is not None and not pd.isna(t["realized_return_pct"])
                                else None
                            ),
                            holding_days=(
                                round(float(t["holding_days"]), 1)
                                if t.get("holding_days") is not None and not pd.isna(t["holding_days"])
                                else None
                            ),
                            reason=str(t.get("reason", "")),
                        )
                    )
            parsed_individual[sym] = IndividualResultItem(
                metrics=BacktestMetricsSchema(**ind["metrics"]) if isinstance(ind.get("metrics"), dict) else ind.get("metrics"),
                equity_curve=sym_pts,
                trades=sym_trades,
            )

        return PortfolioBacktestResponse(
            scope_type=req.scope_type.value,
            scope_target=scope_target,
            start_date=req.start_date,
            end_date=req.end_date,
            symbols_count=len(res["symbols_breakdown"]),
            aggregate_metrics=BacktestMetricsSchema(**res["aggregate_metrics"]),
            portfolio_equity_curve=[
                EquityCurvePoint(**pt) for pt in res["portfolio_equity_curve"]
            ],
            symbols_breakdown=[
                SymbolBreakdownItem(**item) for item in res["symbols_breakdown"]
            ],
            individual_results=parsed_individual,
        )
    except HTTPException:
        raise
    except Exception as err:
        logger.exception("Lỗi chạy kiểm thử danh mục")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi thực thi kiểm thử chiến lược: {err!s}",
        )

