"""Router quản lý các endpoint mô phỏng kiểm thử chiến lược đầu tư (Backtesting Engine)."""

from fastapi import APIRouter, Query

from app.models.schemas import BacktestRequest, BacktestResponse, BacktestSummaryResponse
from app.services import backtest_service

router = APIRouter(prefix="/backtest", tags=["Backtesting Engine"])


@router.post(
    "/run",
    response_model=BacktestResponse,
    summary="Chạy mô phỏng Backtesting chiến lược đầu tư thực tế",
    description="Chạy kiểm thử có tính toán chu kỳ thanh toán T+2, thuế bán 0.10%, phí mua/bán 0.15% và lô chẵn 100.",
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
