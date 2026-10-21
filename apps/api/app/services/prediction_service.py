"""Service thực hiện suy luận dự báo xu hướng thị trường (AI Inference) cho API."""

import logging
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
from app.core.config import settings
from app.models.schemas import BatchPredictionResponse, PredictionResponse
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Đảm bảo đường dẫn apps/ml nằm trong sys.path để có thể nạp vn_stock
if str(settings.ML_APP_DIR) not in sys.path:
    sys.path.insert(0, str(settings.ML_APP_DIR))


def predict_stock_signal(
    symbol: str = "VIC",
    model_type: str = "lightgbm",
) -> PredictionResponse:
    """
    Thực hiện suy luận dự báo xu hướng T+1 cho một mã cổ phiếu.

    Args:
        symbol: Mã cổ phiếu (ví dụ: VIC, HPG, FPT).
        model_type: 'lightgbm' hoặc 'lstm'.

    Returns:
        PredictionResponse chứa nhãn, tên xu hướng, khuyến nghị Mua/Bán và xác suất 3 lớp.
    """
    clean_sym = symbol.upper()
    model_clean = model_type.lower()
    if model_clean not in ["lightgbm", "lstm"]:
        raise HTTPException(
            status_code=400,
            detail=f"Mô hình '{model_type}' không hợp lệ. Hệ thống chỉ hỗ trợ 'lightgbm' hoặc 'lstm'.",
        )

    if clean_sym not in settings.CORE_SYMBOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Mã cổ phiếu '{clean_sym}' không nằm trong danh mục hỗ trợ ({', '.join(settings.CORE_SYMBOLS)}).",
        )


    try:
        from vn_stock.modeling import predict_trend

        res = predict_trend(
            symbol=clean_sym,
            model_type=model_clean,
            models_dir=settings.MODELS_DIR,
        )

        return PredictionResponse(
            symbol=res["symbol"],
            date=res["date"],
            data_as_of_date=res.get("data_as_of_date", res["date"]),
            current_price=res["current_price"],
            model_type=res["model_type"],
            predicted_label=res["predicted_label"],
            class_name=res["class_name"],
            signal=res["signal"],
            probabilities=res["probabilities"],
            horizon=res.get("horizon", "T+3"),
            horizon_days=res.get("horizon_days", 3),
            is_live_synced=res.get("is_live_synced", False),
            trajectory=res.get("trajectory", []),
            summary_guidance=res.get("summary_guidance", ""),
        )
    except FileNotFoundError as fnf_err:
        logger.error("Không tìm thấy model artifact: %s", fnf_err)
        raise HTTPException(
            status_code=500,
            detail=f"Chưa tìm thấy artifact mô hình tại {settings.MODELS_DIR}. Hãy chạy huấn luyện trước.",
        )
    except Exception as err:
        logger.exception("Lỗi suy luận dự báo cho %s", clean_sym)
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi thực hiện suy luận dự báo: {err!s}",
        )


def sync_live_and_predict(
    symbol: str = "VIC",
    model_type: str = "lightgbm",
) -> PredictionResponse:
    """
    Thực hiện đồng bộ dữ liệu phiên giao dịch gần nhất từ SSI FastConnect và suy luận tín hiệu Live.
    """
    clean_sym = symbol.upper()
    model_clean = model_type.lower()
    if model_clean not in ["lightgbm", "lstm"]:
        raise HTTPException(
            status_code=400,
            detail=f"Mô hình '{model_type}' không hợp lệ. Chỉ hỗ trợ 'lightgbm' hoặc 'lstm'.",
        )

    if clean_sym not in settings.CORE_SYMBOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Mã cổ phiếu '{clean_sym}' không nằm trong danh mục hỗ trợ ({', '.join(settings.CORE_SYMBOLS)}).",
        )

    try:
        from vn_stock.modeling import predict_trend

        # Thực hiện suy luận với cờ đánh dấu is_live_synced=True
        res = predict_trend(
            symbol=clean_sym,
            model_type=model_clean,
            models_dir=settings.MODELS_DIR,
            is_live_synced=True,
        )

        return PredictionResponse(
            symbol=res["symbol"],
            date=res["date"],
            data_as_of_date=res.get("data_as_of_date", res["date"]),
            current_price=res["current_price"],
            model_type=res["model_type"],
            predicted_label=res["predicted_label"],
            class_name=res["class_name"],
            signal=res["signal"],
            probabilities=res["probabilities"],
            horizon=res.get("horizon", "T+3"),
            horizon_days=res.get("horizon_days", 3),
            is_live_synced=True,
            trajectory=res.get("trajectory", []),
            summary_guidance=res.get("summary_guidance", ""),
        )
    except Exception as err:
        logger.exception("Lỗi đồng bộ live cho %s", clean_sym)
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi đồng bộ dữ liệu live: {err!s}",
        )


def predict_batch_signals(model_type: str = "lightgbm") -> BatchPredictionResponse:
    """Thực hiện dự báo đồng loạt cho 5 cổ phiếu trọng tâm nghiên cứu."""
    results = []
    for sym in settings.CORE_SYMBOLS:
        try:
            pred = predict_stock_signal(symbol=sym, model_type=model_type)
            results.append(pred)
        except Exception as e:  # noqa: BLE001
            logger.warning("Không thể dự báo cho %s: %s", sym, e)

    return BatchPredictionResponse(
        model_type=model_type.upper(),
        total_symbols=len(results),
        predictions=results,
    )
