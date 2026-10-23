"""Router quản lý các endpoint mô phỏng kiểm thử chiến lược đầu tư (Backtesting Engine)."""

from fastapi import APIRouter, Query

from app.models.schemas import (
    AdvancedBacktestRequest,
    BacktestRequest,
    BacktestResponse,
    BacktestSummaryResponse,
    PortfolioBacktestResponse,
    RecentSignalsResponse,
    StrategyPresetsResponse,
)
from app.services import backtest_service

router = APIRouter(prefix="/backtest", tags=["Backtesting Engine"])


@router.post(
    "/run-advanced",
    response_model=PortfolioBacktestResponse,
    summary="Chạy kiểm thử chiến lược toàn diện cho Rổ chỉ số, Ngành hoặc Danh mục (chuẩn DNSE)",
    description="Kiểm thử trên phạm vi Rổ chỉ số (VN30, VN100), Cổ phiếu đơn lẻ, Ngành nghề hoặc Danh mục tự chọn trong dải ngày <= 1 năm kèm bộ điều kiện Mua/Bán chi tiết.",
)
async def run_advanced_simulation(
    request: AdvancedBacktestRequest,
) -> PortfolioBacktestResponse:
    """Endpoint thực thi backtest danh mục đa mã và bộ lọc điều kiện theo chuẩn DNSE."""
    return backtest_service.run_advanced_backtest(request)



@router.get(
    "/presets",
    response_model=StrategyPresetsResponse,
    summary="Danh mục 8 chiến thuật mẫu chuẩn DNSE",
    description="Truy vấn danh mục 8 chiến thuật mẫu thực chiến có sẵn cấu hình và chỉ số hiệu suất.",
)
async def get_presets() -> StrategyPresetsResponse:
    """Endpoint cung cấp danh sách chiến thuật mẫu."""
    return backtest_service.get_presets_service()


@router.get(
    "/signals/recent",
    response_model=RecentSignalsResponse,
    summary="Danh sách tín hiệu Mua/Bán mới nhất near-realtime",
    description="Truy vấn các tín hiệu giao dịch mới phát sinh theo chuẩn bảng tín hiệu DNSE.",
)
async def get_recent_signals() -> RecentSignalsResponse:
    """Endpoint cung cấp bảng tín hiệu giao dịch mới nhất."""
    return backtest_service.get_recent_signals_service()


@router.post(
    "/run",
    response_model=BacktestResponse,
    summary="Chạy mô phỏng Backtesting chiến lược đầu tư thực tế",
    description="Chạy kiểm thử có tính toán chu kỳ thanh toán T+2, thuế bán 0.10%, phí mua/bán 0.15%, lô chẵn 100 và quy tắc quản trị rủi ro Stop Loss, Take Profit, Trailing Stop.",
)
async def run_simulation(
    request: BacktestRequest,
) -> BacktestResponse:
    """Endpoint thực thi backtest tương tác từ Dashboard."""
    return backtest_service.run_backtest_simulation(request)


@router.get(
    "/summary",
    response_model=BacktestSummaryResponse,
    summary="Bảng tổng hợp hiệu quả Backtest OOS trên các mã cổ phiếu",
    description="Truy vấn kết quả so sánh ROI, Sharpe, Sortino, MDD và Win Rate trên danh mục 5 mã trọng tâm.",
)
async def get_summary(
    model_type: str = Query("lightgbm", description="Loại mô hình AI ('lightgbm' hoặc 'lstm')"),
) -> BacktestSummaryResponse:
    """Endpoint lấy bảng tổng hợp đối chứng hiệu quả đầu tư."""
    return backtest_service.get_backtest_summary(model_type=model_type)
