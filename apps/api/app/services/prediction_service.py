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
    Thực hiện suy luận dự báo xu hướng chu kỳ T+3 và Quỹ đạo 3 phiên cho một mã cổ phiếu.

    Args:
        symbol: Mã cổ phiếu (ví dụ: VIC, HPG, FPT).
        model_type: 'lightgbm' hoặc 'lstm'.

    Returns:
        PredictionResponse chứa nhãn, tên xu hướng, khuyến nghị Mua/Bán, xác suất 3 lớp và Quỹ đạo 3 phiên (T+1 -> T+3).
    """
    clean_sym = symbol.upper()
    model_clean = model_type.lower()
    if model_clean not in ["lightgbm", "lstm"]:
        raise HTTPException(
            status_code=400,
            detail=f"Mô hình '{model_type}' không hợp lệ. Hệ thống chỉ hỗ trợ 'lightgbm' hoặc 'lstm'.",
        )

    try:
        from vn_stock.modeling import predict_trend

        res = predict_trend(
            symbol=clean_sym,
            model_type=model_clean,
            models_dir=settings.MODELS_DIR,
        )

        session_info = get_market_sync_status()
        session_label = session_info.get("status_label", "")

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
            market_session_label=res.get("market_session_label", session_label),
            session_info=session_info,
            trajectory=res.get("trajectory", []),
            summary_guidance=res.get("summary_guidance", ""),
            training_info=res.get("training_info"),
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

    try:
        from vn_stock.data_ingestion import fetch_stock_data
        from vn_stock.modeling import predict_trend

        # 1. Kích hoạt đồng bộ nến mới nhất tới T hoặc T-1 qua data_ingestion
        try:
            fetch_stock_data(clean_sym)
        except Exception as sync_err:
            logger.warning("Không thể kéo SSI trực tiếp cho %s, sử dụng dữ liệu cục bộ: %s", clean_sym, sync_err)

        # 2. Thực hiện suy luận với cờ đánh dấu is_live_synced=True
        res = predict_trend(
            symbol=clean_sym,
            model_type=model_clean,
            models_dir=settings.MODELS_DIR,
            is_live_synced=True,
        )

        session_info = get_market_sync_status()
        session_label = session_info.get("status_label", "")

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
            market_session_label=res.get("market_session_label", session_label),
            session_info=session_info,
            trajectory=res.get("trajectory", []),
            summary_guidance=res.get("summary_guidance", ""),
            training_info=res.get("training_info"),
        )
    except Exception as err:
        logger.exception("Lỗi đồng bộ live cho %s", clean_sym)
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi đồng bộ dữ liệu live: {err!s}",
        )


def retrain_production_system(
    horizon: int = 3,
    threshold: float = 0.02,
    val_buffer_days: int = 40,
    scope: str = "VN30",
) -> dict:
    """
    Kích hoạt quy trình huấn luyện lại mô hình thực chiến T+horizon:
    - Thu thập dữ liệu nến mới nhất tới phiên T-1 (hoặc T sau 15:00)
    - Tự động huấn luyện lại LightGBM và LSTM trên toàn bộ rổ VN30 (30 mã)
    - Cập nhật artifacts models/
    """
    try:
        from vn_stock.modeling.train import train_production_model

        symbols_arg = "VN30" if scope.upper() != "CORE" else None
        summary = train_production_model(
            symbols=symbols_arg,
            horizon=horizon,
            threshold=threshold,
            val_buffer_days=val_buffer_days,
            save_artifacts=True,
            models_dir=settings.MODELS_DIR,
        )
        return summary
    except Exception as err:
        logger.exception("Lỗi khi huấn luyện lại mô hình thực chiến")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi huấn luyện lại mô hình thực chiến: {err!s}",
        )


def predict_batch_signals(
    model_type: str = "lightgbm",
    symbols: list[str] | None = None,
    scope: str = "VN30",
) -> BatchPredictionResponse:
    """Thực hiện dự báo đồng loạt cho danh mục cổ phiếu (mặc định toàn bộ 30 mã VN30 hoặc 5 mã CORE)."""
    if symbols is not None and len(symbols) > 0:
        target_symbols = [s.upper() for s in symbols]
    elif scope.upper() == "CORE":
        target_symbols = settings.CORE_SYMBOLS
    else:
        target_symbols = getattr(settings, "VN30_SYMBOLS", settings.CORE_SYMBOLS)

    results = []
    for sym in target_symbols:
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


def get_market_sync_status() -> dict:
    """Trả về trạng thái phiên giao dịch hiện tại và tiến trình đồng bộ dữ liệu."""
    try:
        from vn_stock.market_session import get_target_market_session_info
        return get_target_market_session_info()
    except Exception as e:
        logger.warning("Không thể lấy session info: %s", e)
        return {"status": "unknown", "error": str(e)}


def trigger_market_sync(force: bool = False) -> dict:
    """Kích hoạt thủ công tiến trình đồng bộ toàn bộ nến thị trường phiên gần nhất."""
    try:
        from vn_stock.data_ingestion import sync_latest_market_data
        return sync_latest_market_data(force=force)
    except Exception as e:
        logger.exception("Lỗi kích hoạt đồng bộ thị trường")
        raise HTTPException(status_code=500, detail=f"Lỗi khi đồng bộ dữ liệu: {e}")
