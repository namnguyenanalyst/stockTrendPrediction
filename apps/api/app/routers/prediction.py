"""Router quản lý các endpoint suy luận dự báo xu hướng thị trường (AI Inference)."""

from fastapi import APIRouter, Query

from app.models.schemas import BatchPredictionResponse, PredictionResponse
from app.services import prediction_service

router = APIRouter(prefix="/predict", tags=["AI Prediction"])


@router.get(
    "/signal",
    response_model=PredictionResponse,
    summary="Dự báo xu hướng T+1 cho một mã cổ phiếu",
    description="Thực hiện suy luận bằng mô hình LightGBM hoặc PyTorch Global LSTM, trả về xác suất 3 lớp và khuyến nghị Mua/Bán.",
)
async def predict_signal(
    symbol: str = Query("VIC", description="Mã cổ phiếu cần dự báo (ví dụ: VIC, HPG, FPT)"),
    model_type: str = Query("lightgbm", description="Loại mô hình AI ('lightgbm' hoặc 'lstm')"),
) -> PredictionResponse:
    """Endpoint suy luận tín hiệu đầu tư cho một mã."""
    return prediction_service.predict_stock_signal(
        symbol=symbol,
        model_type=model_type,
    )


@router.get(
    "/batch",
    response_model=BatchPredictionResponse,
    summary="Dự báo đồng loạt cho 5 cổ phiếu trọng tâm",
    description="Chạy dự báo xu hướng song song cho danh mục 5 mã VN30: VIC, HPG, FPT, VNM, MWG.",
)
async def predict_batch(
    model_type: str = Query("lightgbm", description="Loại mô hình AI ('lightgbm' hoặc 'lstm')"),
) -> BatchPredictionResponse:
    """Endpoint dự báo danh mục 5 mã trọng tâm."""
    return prediction_service.predict_batch_signals(model_type=model_type)
