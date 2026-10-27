"""Kiểm thử tự động cho subpackage vn_stock.modeling."""

import pickle
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler
import torch

from vn_stock.config import NUM_CLASSES
from vn_stock.features import ALL_FEATURE_COLS, FEATURE_COLS
from vn_stock.modeling.model import (
    GlobalLSTMClassifier,
    PredictionModel,
    create_lightgbm_model,
)
from vn_stock.modeling.predict import (
    load_prediction_artifacts,
    predict_next_day,
    predict_trend,
    prepare_inference_features,
)
from vn_stock.modeling.train import (
    evaluate_predictions,
    train_lstm_model,
    train_production_model,
)


@pytest.fixture
def mock_panel_data():
    """Tạo tập dữ liệu mock giả lập 2 mã cổ phiếu phục vụ kiểm thử nhanh."""
    dates = pd.date_range("2023-01-01", periods=60, freq="B")
    records = []
    for sym_idx, sym in enumerate(["VIC", "HPG"]):
        for i, dt in enumerate(dates):
            row = {
                "Date": dt,
                "Symbol": sym,
                "Close": 50.0 + i * 0.1 + sym_idx * 5.0,
                "Label": i % 3,  # Nhãn 0, 1, 2
            }
            # Tạo 13 đặc trưng số học
            for f in FEATURE_COLS:
                row[f] = np.sin(i * 0.2 + sym_idx) * 0.05
            row["Symbol_Code"] = sym_idx
            records.append(row)
    df = pd.DataFrame(records).sort_values(["Date", "Symbol"]).reset_index(drop=True)
    return df


def test_global_lstm_classifier_architecture():
    """Kiểm thử cấu trúc mạng GlobalLSTMClassifier và tính toán xác suất Softmax."""
    batch_size = 16
    seq_len = 20
    input_size = len(ALL_FEATURE_COLS)

    model = GlobalLSTMClassifier(
        input_size=input_size,
        hidden_size=32,
        num_layers=2,
        num_classes=NUM_CLASSES,
        dropout=0.2,
    )
    model.eval()

    x = torch.randn(batch_size, seq_len, input_size)
    logits = model(x)
    assert logits.shape == (batch_size, NUM_CLASSES)

    probs = model.predict_proba(x)
    assert probs.shape == (batch_size, NUM_CLASSES)
    # Tổng xác suất mỗi mẫu phải xấp xỉ 1.0
    row_sums = probs.sum(dim=1).detach().numpy()
    np.testing.assert_allclose(row_sums, 1.0, atol=1e-5)


def test_prediction_model_interface():
    """Kiểm thử mô hình hồi quy đơn biến cũ PredictionModel (tương thích ngược)."""
    model = PredictionModel(input_size=len(ALL_FEATURE_COLS), output_size=1)
    x = torch.randn(4, 10, len(ALL_FEATURE_COLS))
    out = model(x)
    assert out.shape == (4, 1)


def test_create_lightgbm_model_defaults_and_custom():
    """Kiểm thử khởi tạo mô hình LightGBM với siêu tham số mặc định và tùy chỉnh."""
    model_def = create_lightgbm_model()
    assert model_def.n_estimators == 300
    assert model_def.learning_rate == 0.03

    model_custom = create_lightgbm_model({"n_estimators": 100, "max_depth": 3})
    assert model_custom.n_estimators == 100
    assert model_custom.max_depth == 3


def test_evaluate_predictions_metrics_integrity():
    """Kiểm thử tính toán đầy đủ các metrics đánh giá phân loại đa lớp."""
    y_true = np.array([0, 1, 2, 0, 1, 2, 2, 1])
    y_pred = np.array([0, 1, 2, 0, 1, 1, 2, 0])

    metrics = evaluate_predictions(y_true, y_pred)
    assert "accuracy" in metrics
    assert "macro_f1" in metrics
    assert "weighted_f1" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["accuracy"] == 6 / 8
    assert len(metrics["confusion_matrix"]) == 3


def test_predict_trend_with_artifacts(tmp_path, mock_panel_data):
    """Kiểm thử chức năng suy luận predict_trend với artifacts giả lập."""
    # 1. Tạo mock artifacts
    scaler = StandardScaler()
    scaler.fit(mock_panel_data[FEATURE_COLS])
    scaler_path = tmp_path / "scaler_window3.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    # Mock LSTM
    from vn_stock.config import DEFAULT_LSTM_HIDDEN_SIZE, DEFAULT_LSTM_NUM_LAYERS
    lstm_model = GlobalLSTMClassifier(
        input_size=len(ALL_FEATURE_COLS),
        hidden_size=DEFAULT_LSTM_HIDDEN_SIZE,
        num_layers=DEFAULT_LSTM_NUM_LAYERS,
    )
    lstm_path = tmp_path / "global_lstm_classifier.pth"
    torch.save(lstm_model.state_dict(), lstm_path)

    # Mock LightGBM
    lgb_model = create_lightgbm_model({"n_estimators": 5, "min_child_samples": 2})
    lgb_model.fit(mock_panel_data[ALL_FEATURE_COLS], mock_panel_data["Label"])
    lgb_path = tmp_path / "lightgbm_classifier.pkl"
    with open(lgb_path, "wb") as f:
        pickle.dump(lgb_model, f)

    # 2. Test load_prediction_artifacts
    loaded_lstm, _ = load_prediction_artifacts(
        "lstm", models_dir=tmp_path
    )
    assert isinstance(loaded_lstm, GlobalLSTMClassifier)

    loaded_lgb, _ = load_prediction_artifacts("lightgbm", models_dir=tmp_path)
    assert hasattr(loaded_lgb, "predict_proba")

    # 3. Test predict_trend với mock features
    with patch("vn_stock.modeling.predict.prepare_inference_features") as mock_prep:
        mock_prep.return_value = (mock_panel_data, 55.0, "2023-03-31")

        # Test dự báo với LSTM
        res_lstm = predict_trend(
            symbol="VIC",
            model_type="lstm",
            seq_length=10,
            models_dir=tmp_path,
        )

        assert res_lstm["symbol"] == "VIC"
        assert res_lstm["model_type"] == "lstm"
        assert res_lstm["predicted_label"] in (0, 1, 2)
        assert res_lstm["class_name"] in ("GIẢM", "ĐI NGANG", "TĂNG")
        assert res_lstm["signal"] in ("BÁN (SELL)", "NẮM GIỮ (HOLD)", "MUA (BUY)")
        assert len(res_lstm["probabilities"]) == 3

        # Test dự báo với LightGBM
        res_lgb = predict_trend(symbol="VIC", model_type="lightgbm", seq_length=10, models_dir=tmp_path)
        assert res_lgb["symbol"] == "VIC"
        assert res_lgb["model_type"] == "lightgbm"
        assert res_lgb["predicted_label"] in (0, 1, 2)
        assert sum(res_lgb["probabilities"].values()) == pytest.approx(1.0, abs=1e-2)

        # Test live_synced và trajectory 3 phiên
        res_live = predict_trend(
            symbol="VIC",
            model_type="lightgbm",
            seq_length=10,
            models_dir=tmp_path,
            is_live_synced=True,
        )
        assert res_live["is_live_synced"] is True
        assert len(res_live["trajectory"]) == 3
        assert res_live["trajectory"][0]["day_name"] == "T+1"

        # Test predict_next_day tương thích ngược
        res_next = predict_next_day(symbol="VIC", seq_length=10, models_dir=tmp_path)
        assert res_next["symbol"] == "VIC"
        assert "predicted_label" in res_next


def test_predict_trend_unsupported_model_raises(tmp_path, mock_panel_data):
    """Kiểm tra báo lỗi khi model_type không nằm trong danh sách hỗ trợ."""
    scaler = StandardScaler()
    scaler.fit(mock_panel_data[FEATURE_COLS])
    scaler_path = tmp_path / "scaler_window3.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    with pytest.raises(ValueError, match="Loại mô hình không hợp lệ"):
        predict_trend(symbol="VIC", model_type="unsupported_model_xyz", models_dir=tmp_path)


def test_prepare_inference_features_index():
    """Kiểm tra prepare_inference_features cho chỉ số thị trường (VNINDEX)."""
    dates = pd.date_range("2023-01-01", periods=250, freq="B")
    df_vni = pd.DataFrame({
        "Date": dates,
        "VNINDEX_Close": np.linspace(1100.0, 1200.0, 250),
    })

    with (
        patch("vn_stock.modeling.predict.load_local_data", return_value=df_vni),
        patch("vn_stock.modeling.predict.get_target_market_date", return_value="2023-12-29"),
    ):
        df_feat, latest_close, latest_date = prepare_inference_features("VNINDEX", seq_length=10)
        assert len(df_feat) >= 10
        assert latest_close > 0
        assert latest_date is not None
        for col in ALL_FEATURE_COLS:
            assert col in df_feat.columns


def test_train_production_model(tmp_path):
    """Kiểm tra quy trình huấn luyện lại mô hình sản xuất train_production_model."""
    dates = pd.date_range("2023-01-01", periods=250, freq="B")
    records = []
    for d in dates:
        row = {
            "Date": d,
            "Symbol": "VIC",
            "Open": 50.0 + np.random.randn(),
            "High": 52.0 + np.random.randn(),
            "Low": 48.0 + np.random.randn(),
            "Close": 51.0 + np.random.randn(),
            "Volume": 1000000,
            "VNINDEX_Return_1d": 0.005,
        }
        records.append(row)
    mock_panel = pd.DataFrame(records)

    with (
        patch("vn_stock.data_ingestion.sync_latest_market_data", return_value={"status": "success"}),
        patch("vn_stock.modeling.train.build_panel_dataset", return_value=mock_panel),
    ):
        res = train_production_model(
            symbols=["VIC"],
            horizon=3,
            threshold=0.02,
            val_buffer_days=10,
            epochs=1,
            seq_length=5,
            save_artifacts=True,
            models_dir=tmp_path,
        )

        assert "lightgbm_metrics" in res
        assert "lstm_metrics" in res
        assert "horizon" in res
        assert res["horizon"] == "T+3"
        assert (tmp_path / "production_lgb_t3.txt").exists()
        assert (tmp_path / "production_lstm_t3.pth").exists()
        assert (tmp_path / "production_scaler_t3.pkl").exists()
        assert (tmp_path / "production_training_info_t3.json").exists()


def test_train_lstm_model_wrapper(tmp_path):
    """Kiểm tra hàm train_lstm_model gọi train_production_model và trả về mô hình."""
    mock_summary = {
        "status": "success",
        "lstm_metrics": {"macro_f1": 0.55},
    }
    with patch("vn_stock.modeling.train.train_production_model", return_value=mock_summary):
        model, f1 = train_lstm_model(symbol="VIC", epochs=1, models_dir=tmp_path)
        assert isinstance(model, GlobalLSTMClassifier)
        assert f1 == 0.55
