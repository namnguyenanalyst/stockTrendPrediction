"""Service thực hiện suy luận dự báo xu hướng thị trường (AI Inference) cho API."""

import logging
import os
import sys
from time import perf_counter

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
from fastapi import HTTPException
import pandas as pd

from app.core.config import settings
from app.core.validation import normalize_symbol
from app.models.schemas import BatchPredictionResponse, PredictionResponse

logger = logging.getLogger(__name__)


def _log_prediction(response: PredictionResponse, started: float) -> None:
    info = response.training_info or {}
    context = dict(event='prediction_completed', symbol=response.symbol,
                   model_type=response.model_type, data_as_of_date=response.data_as_of_date,
                   artifact_generation=info.get('artifact_generation', 'unknown'),
                   serving_status=info.get('serving_status', 'unknown'),
                   elapsed_ms=round((perf_counter() - started) * 1000, 2))
    logger.info('prediction_completed symbol=%s model=%s data_as_of=%s generation=%s status=%s elapsed_ms=%s',
                context['symbol'], context['model_type'], context['data_as_of_date'],
                context['artifact_generation'], context['serving_status'], context['elapsed_ms'], extra=context)

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
    clean_sym = normalize_symbol(symbol)
    model_clean = model_type.strip().lower()
    if model_clean not in ["lightgbm", "lstm"]:
        raise HTTPException(
            status_code=400,
            detail=f"Mô hình '{model_type}' không hợp lệ. Hệ thống chỉ hỗ trợ 'lightgbm' hoặc 'lstm'.",
        )

    started = perf_counter()
    try:
        from vn_stock.modeling import predict_trend

        res = predict_trend(
            symbol=clean_sym,
            model_type=model_clean,
            models_dir=settings.MODELS_DIR,
        )

        session_info = get_market_sync_status()
        session_label = session_info.get("status_label", "")

        response = PredictionResponse(
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
            data_quality=res.get("data_quality"),
        )
        _log_prediction(response, started)
        return response
    except FileNotFoundError as fnf_err:
        logger.error("Không tìm thấy model artifact: %s", fnf_err)
        raise HTTPException(
            status_code=503,
            detail="Chưa tìm thấy artifact mô hình. Hãy chạy huấn luyện trước.",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Lỗi suy luận dự báo symbol=%s model=%s", clean_sym, model_clean)
        raise HTTPException(
            status_code=500,
            detail="Lỗi khi thực hiện suy luận dự báo.",
        )


def sync_live_and_predict(
    symbol: str = "VIC",
    model_type: str = "lightgbm",
) -> PredictionResponse:
    """
    Tải snapshot SSI cho yêu cầu và suy luận Live mà không ghi cache dùng chung.
    """
    clean_sym = normalize_symbol(symbol)
    model_clean = model_type.strip().lower()
    if model_clean not in ["lightgbm", "lstm"]:
        raise HTTPException(
            status_code=400,
            detail=f"Mô hình '{model_type}' không hợp lệ. Chỉ hỗ trợ 'lightgbm' hoặc 'lstm'.",
        )

    started = perf_counter()
    try:
        from vn_stock.data_ingestion import fetch_live_prediction_panel
        from vn_stock.market_session import get_target_market_date
        from vn_stock.modeling import predict_trend

        # Do not label a fallback cache prediction as a successful live sync.
        target_date = get_target_market_date()
        try:
            synced = fetch_live_prediction_panel(clean_sym, target_date)
        except Exception as sync_err:
            logger.warning("Không thể kéo SSI trực tiếp cho %s: %s", clean_sym, sync_err)
            raise HTTPException(503, "Không thể đồng bộ dữ liệu live; hãy dùng dự báo từ cache.") from None
        if synced is None or synced.empty or pd.to_datetime(synced["Date"]).max() < pd.Timestamp(target_date):
            raise HTTPException(503, "Dữ liệu chưa cập nhật tới phiên chốt gần nhất.")

        # 2. Thực hiện suy luận với cờ đánh dấu is_live_synced=True
        res = predict_trend(
            symbol=clean_sym,
            model_type=model_clean,
            models_dir=settings.MODELS_DIR,
            is_live_synced=True,
            raw_snapshot=synced,
        )
        if res.get("data_as_of_date", res["date"]) != target_date:
            raise HTTPException(503, "Dự báo chưa sử dụng đủ dữ liệu của phiên chốt gần nhất.")

        session_info = get_market_sync_status()
        session_label = session_info.get("status_label", "")

        response = PredictionResponse(
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
            data_quality=res.get("data_quality"),
        )
        _log_prediction(response, started)
        return response
    except HTTPException:
        raise
    except Exception:
        logger.exception("Lỗi đồng bộ live cho %s", clean_sym)
        raise HTTPException(
            status_code=500,
            detail="Lỗi khi đồng bộ dữ liệu live.",
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

        symbols_arg = "CORE" if scope.upper() == "CORE" else "VN30"
        summary = train_production_model(
            symbols=symbols_arg,
            horizon=horizon,
            threshold=threshold,
            val_buffer_days=val_buffer_days,
            save_artifacts=True,
            models_dir=settings.MODELS_DIR,
        )
        return summary
    except Exception:
        logger.exception("Lỗi khi huấn luyện lại mô hình thực chiến")
        raise HTTPException(
            status_code=500,
            detail="Lỗi khi huấn luyện lại mô hình thực chiến.",
        )


def predict_batch_signals(
    model_type: str = "lightgbm",
    symbols: list[str] | None = None,
    scope: str = "VN30",
) -> BatchPredictionResponse:
    """Thực hiện dự báo đồng loạt cho danh mục cổ phiếu (mặc định toàn bộ 30 mã VN30 hoặc 5 mã CORE)."""
    if model_type.strip().lower() not in ("lightgbm", "lstm"):
        raise HTTPException(400, "Mô hình không hợp lệ.")
    if scope.upper() not in ("CORE", "VN30"):
        raise HTTPException(400, "Phạm vi không hợp lệ.")
    if symbols is not None and len(symbols) > 0:
        if len(symbols) > 100:
            raise HTTPException(400, "Danh mục tối đa 100 mã.")
        target_symbols = list(dict.fromkeys(normalize_symbol(s) for s in symbols))
    elif scope.upper() == "CORE":
        target_symbols = settings.CORE_SYMBOLS
    else:
        target_symbols = getattr(settings, "VN30_SYMBOLS", settings.CORE_SYMBOLS)

    results = []
    errors = []
    for sym in target_symbols:
        try:
            pred = predict_stock_signal(symbol=sym, model_type=model_type)
            results.append(pred)
        except Exception as e:  # noqa: BLE001
            logger.warning("Không thể dự báo cho %s: %s", sym, e)
            errors.append({"symbol": sym, "status_code": e.status_code if isinstance(e, HTTPException) else 500,
                           "detail": "Không thể tạo dự báo cho mã này."})

    return BatchPredictionResponse(
        model_type=model_type.upper(),
        total_symbols=len(results),
        requested_symbols=len(target_symbols),
        errors=errors,
        predictions=results,
    )


def get_market_sync_status() -> dict:
    """Trả về trạng thái phiên giao dịch hiện tại và tiến trình đồng bộ dữ liệu."""
    try:
        from vn_stock.market_session import get_target_market_session_info
        return get_target_market_session_info()
    except Exception as e:
        logger.warning("Không thể lấy session info: %s", e)
        return {"status": "unknown"}


def trigger_market_sync(force: bool = False) -> dict:
    """Kích hoạt thủ công tiến trình đồng bộ toàn bộ nến thị trường phiên gần nhất."""
    try:
        from vn_stock.data_ingestion import sync_latest_market_data
        return sync_latest_market_data(force=force)
    except Exception:
        logger.exception("Lỗi kích hoạt đồng bộ thị trường")
        raise HTTPException(status_code=503, detail="Lỗi khi đồng bộ dữ liệu.")
