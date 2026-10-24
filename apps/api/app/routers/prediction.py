"""Router quản lý các endpoint suy luận dự báo xu hướng thị trường (AI Inference)."""

from fastapi import APIRouter, Query

from pydantic import BaseModel, Field

from app.models.schemas import BatchPredictionResponse, LiveSyncRequest, PredictionResponse
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


@router.post(
    "/live",
    response_model=PredictionResponse,
    summary="Đồng bộ dữ liệu phiên gần nhất và dự báo Live chu kỳ T+3 (POST)",
    description="Kết nối dữ liệu mới nhất (Near-realtime) và xuất tín hiệu khuyến nghị cho chu kỳ T+3 cùng Quỹ đạo 3 phiên.",
)
async def predict_live_post(request: LiveSyncRequest) -> PredictionResponse:
    """Endpoint đồng bộ và suy luận trực tuyến nhận body JSON."""
    return prediction_service.sync_live_and_predict(
        symbol=request.symbol,
        model_type=request.model_type,
    )


@router.get(
    "/live",
    response_model=PredictionResponse,
    summary="Đồng bộ dữ liệu phiên gần nhất và dự báo Live chu kỳ T+3 (GET)",
    description="Kết nối dữ liệu mới nhất (Near-realtime) và xuất tín hiệu khuyến nghị cho chu kỳ T+3 cùng Quỹ đạo 3 phiên qua GET query.",
)
async def predict_live_get(
    symbol: str = Query("VIC", description="Mã cổ phiếu cần dự báo (ví dụ: VIC, HPG, FPT)"),
    model_type: str = Query("lightgbm", description="Loại mô hình AI ('lightgbm' hoặc 'lstm')"),
) -> PredictionResponse:
    """Endpoint đồng bộ và suy luận trực tuyến qua GET."""
    return prediction_service.sync_live_and_predict(
        symbol=symbol,
        model_type=model_type,
    )


class RetrainRequest(BaseModel):
    horizon: int = Field(default=3, description="Chân trời dự báo (mặc định 3 phiên T+3)")
    threshold: float = Field(default=0.02, description="Ngưỡng biến động giá (mặc định 2.0%)")
    val_buffer_days: int = Field(default=40, description="Số phiên đệm validation Early Stopping")
    scope: str = Field(default="VN30", description="Phạm vi danh mục ('VN30' toàn bộ 30 mã)")


@router.post(
    "/retrain",
    summary="Huấn luyện lại mô hình thực chiến T+3 (POST)",
    description="Tự động thu thập dữ liệu tới phiên T-1 (hoặc T sau 15:00) và huấn luyện lại LightGBM + PyTorch LSTM trên toàn bộ dữ liệu tích lũy.",
)
async def retrain_model_endpoint(
    request: RetrainRequest = RetrainRequest(),
) -> dict:
    """Endpoint kích hoạt huấn luyện lại mô hình sản xuất."""
    return prediction_service.retrain_production_system(
        horizon=request.horizon,
        threshold=request.threshold,
        val_buffer_days=request.val_buffer_days,
        scope=request.scope,
    )


