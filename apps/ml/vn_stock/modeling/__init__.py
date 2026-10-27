"""Subpackage xây dựng kiến trúc mô hình, huấn luyện thực chiến (Production Retraining) và dự báo xu hướng."""

__all__ = [
    "GlobalLSTMClassifier",
    "PredictionModel",
    "create_lightgbm_model",
    "evaluate_predictions",
    "predict_next_day",
    "predict_trend",
    "train_lstm_model",
    "train_production_model",
]


def __getattr__(name: str):
    if name in ("GlobalLSTMClassifier", "PredictionModel", "create_lightgbm_model"):
        from vn_stock.modeling import model

        return getattr(model, name)
    elif name in ("predict_next_day", "predict_trend"):
        from vn_stock.modeling import predict

        return getattr(predict, name)
    elif name in (
        "evaluate_predictions",
        "train_lstm_model",
        "train_production_model",
    ):
        from vn_stock.modeling import train

        return getattr(train, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
