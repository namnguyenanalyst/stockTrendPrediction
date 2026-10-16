"""Router quản lý các endpoint suy luận dự báo xu hướng thị trường (AI Inference)."""

from fastapi import APIRouter, Query

from pydantic import BaseModel, Field

from app.models.schemas import BatchPredictionResponse, PredictionResponse
from app.services import prediction_service

router = APIRouter(prefix="/predict", tags=["AI Prediction"])


class PredictionSignalRequest(BaseModel):
    symbol: str = Field(default="VIC", description="Mã cổ phiếu cần dự báo (ví dụ: VIC, HPG, FPT)")
    model_type: str = Field(default="lightgbm", description="Loại mô hình AI ('lightgbm' hoặc 'lstm')")


class BatchPredictionRequest(BaseModel):
    model_type: str = Field(default="lightgbm", description="Loại mô hình AI ('lightgbm' hoặc 'lstm')")


@router.get(
    "/signal",
    response_model=PredictionResponse,
    summary="Dự báo xu hướng T+1 cho một mã cổ phiếu (GET)",
    description="Thực hiện suy luận bằng mô hình LightGBM hoặc PyTorch Global LSTM, trả về xác suất 3 lớp và khuyến nghị Mua/Bán.",
)
async def predict_signal(
    symbol: str = Query("VIC", description="Mã cổ phiếu cần dự báo (ví dụ: VIC, HPG, FPT)"),
    model_type: str = Query("lightgbm", description="Loại mô hình AI ('lightgbm' hoặc 'lstm')"),
) -> PredictionResponse:
    """Endpoint suy luận tín hiệu đầu tư cho một mã qua GET query params."""
    return prediction_service.predict_stock_signal(
        symbol=symbol,
        model_type=model_type,
    )


@router.post(
    "/signal",
    response_model=PredictionResponse,
    summary="Dự báo xu hướng T+1 cho một mã cổ phiếu (POST)",
    description="Thực hiện suy luận bằng mô hình LightGBM hoặc PyTorch Global LSTM nhận body JSON.",
)
async def predict_signal_post(request: PredictionSignalRequest) -> PredictionResponse:
    """Endpoint suy luận tín hiệu đầu tư cho một mã qua POST body."""
    return prediction_service.predict_stock_signal(
        symbol=request.symbol,
        model_type=request.model_type,
    )


@router.get(
    "/batch",
    response_model=BatchPredictionResponse,
    summary="Dự báo đồng loạt cho 5 cổ phiếu trọng tâm (GET)",
    description="Chạy dự báo xu hướng song song cho danh mục 5 mã VN30: VIC, HPG, FPT, VNM, MWG.",
)
async def predict_batch(
    model_type: str = Query("lightgbm", description="Loại mô hình AI ('lightgbm' hoặc 'lstm')"),
) -> BatchPredictionResponse:
    """Endpoint dự báo danh mục 5 mã trọng tâm qua GET."""
    return prediction_service.predict_batch_signals(model_type=model_type)


@router.post(
    "/batch",
    response_model=BatchPredictionResponse,
    summary="Dự báo đồng loạt cho 5 cổ phiếu trọng tâm (POST)",
    description="Chạy dự báo xu hướng song song cho danh mục 5 mã qua POST body.",
)
async def predict_batch_post(
    request: BatchPredictionRequest,
) -> BatchPredictionResponse:
    """Endpoint dự báo danh mục 5 mã trọng tâm qua POST."""
    return prediction_service.predict_batch_signals(model_type=request.model_type)

