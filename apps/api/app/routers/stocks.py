"""Router quản lý các endpoint dữ liệu cổ phiếu và chỉ báo kỹ thuật."""

from fastapi import APIRouter, Query

from app.models.schemas import (
    MarketBoardResponse,
    StockHistoryResponse,
    StockIndicatorsResponse,
    StockSummaryResponse,
    StockSymbolInfo,
)
from app.services import stock_service

router = APIRouter(prefix="/stocks", tags=["Stocks Data"])


@router.get(
    "/symbols",
    response_model=list[StockSymbolInfo],
    summary="Lấy danh sách mã cổ phiếu hỗ trợ",
    description="Trả về danh sách các mã cổ phiếu trong rổ VN30 và thông tin công ty niêm yết.",
)
async def list_symbols() -> list[StockSymbolInfo]:
    """Endpoint trả về danh sách các mã cổ phiếu hợp lệ."""
    return stock_service.get_available_symbols()


@router.get(
    "/history",
    response_model=StockHistoryResponse,
    summary="Truy vấn dữ liệu nến lịch sử OHLCV",
    description="Lấy chuỗi dữ liệu nến lịch sử có phân trang và lọc theo khoảng thời gian.",
)
async def get_history(
    symbol: str = Query("VIC", description="Mã cổ phiếu (ví dụ: VIC, HPG, FPT)"),
    start_date: str | None = Query(None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Ngày kết thúc (YYYY-MM-DD)"),
    limit: int = Query(1500, ge=1, le=5000, description="Số phiên nến tối đa cần lấy"),
) -> StockHistoryResponse:
    """Endpoint truy vấn chuỗi nến OHLCV."""
    return stock_service.get_stock_history(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.get(
    "/indicators",
    response_model=StockIndicatorsResponse,
    summary="Truy vấn các chỉ báo kỹ thuật tương đối",
    description="Lấy chuỗi 13 đặc trưng kỹ thuật tương đối phục vụ vẽ đồ thị và phân tích định lượng.",
)
async def get_indicators(
    symbol: str = Query("VIC", description="Mã cổ phiếu"),
    limit: int = Query(1500, ge=1, le=5000, description="Số phiên tối đa"),
) -> StockIndicatorsResponse:
    """Endpoint truy vấn bộ 13 chỉ báo kỹ thuật."""
    return stock_service.get_stock_indicators(symbol=symbol, limit=limit)


@router.get(
    "/summary",
    response_model=StockSummaryResponse,
    summary="Tóm tắt thông tin thị giá phiên gần nhất",
    description="Trả về thị giá đóng cửa phiên gần nhất, tỷ lệ thay đổi, khối lượng và RSI 14.",
)
async def get_summary(
    symbol: str = Query("VIC", description="Mã cổ phiếu"),
) -> StockSummaryResponse:
    """Endpoint tóm tắt thông tin phiên gần nhất."""
    return stock_service.get_stock_summary(symbol=symbol)


@router.get(
    "/board",
    response_model=MarketBoardResponse,
    summary="Bảng giá điện tử thông minh và tổng quan thị trường",
    description="Trả về dữ liệu bảng giá phong cách Terminal DNSE: các chỉ số thị trường (VNINDEX, VN30...), độ rộng thị trường, danh sách cổ phiếu cùng biểu đồ sparkline, tỷ lệ mua/bán chủ động và nhận định AI.",
)
async def get_market_board() -> MarketBoardResponse:
    """Endpoint truy vấn bảng giá thị trường toàn diện."""
    return stock_service.get_market_board_data()


@router.get(
    "/sync-status",
    summary="Kiểm tra trạng thái phiên giao dịch và đồng bộ nến thị trường",
    description="Trả về ngày chốt phiên gần nhất (T hoặc T-1) và thông tin phiên.",
)
async def get_sync_status() -> dict:
    """Endpoint lấy trạng thái phiên thị trường và nến chốt."""
    from app.services.prediction_service import get_market_sync_status

    return get_market_sync_status()


@router.post(
    "/sync",
    summary="Kích hoạt đồng bộ nến thị trường mới nhất từ SSI FC-Data",
    description="Chủ động kéo nến mới nhất cho VNINDEX và các mã cổ phiếu.",
)
async def trigger_sync() -> dict:
    """Endpoint kích hoạt đồng bộ dữ liệu thị trường."""
    from app.services.prediction_service import trigger_market_sync

    return trigger_market_sync()
