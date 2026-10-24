"""Kiểm thử tự động cho toàn bộ các endpoint của VN Stock FastAPI Backend."""

import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check():
    """Kiểm tra endpoint /health."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "vn-stock-api"
    assert "version" in data


def test_stocks_symbols():
    """Kiểm tra endpoint /api/stocks/symbols."""
    response = client.get("/api/stocks/symbols")
    assert response.status_code == 200
    symbols = response.json()
    assert isinstance(symbols, list)
    assert len(symbols) >= 5

    sym_names = [s["symbol"] for s in symbols]
    for expected in ["VIC", "HPG", "FPT", "VNM", "MWG"]:
        assert expected in sym_names


def test_stocks_history():
    """Kiểm tra endpoint /api/stocks/history."""
    response = client.get("/api/stocks/history?symbol=VIC&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "VIC"
    assert len(data["bars"]) == 10
    first_bar = data["bars"][0]
    for field in ["date", "open", "high", "low", "close", "volume"]:
        assert field in first_bar


def test_stocks_indicators():
    """Kiểm tra endpoint /api/stocks/indicators."""
    response = client.get("/api/stocks/indicators?symbol=VIC&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "VIC"
    assert len(data["indicators"]) == 5
    first_ind = data["indicators"][0]
    for feat in ["close", "open_close_ratio", "sma_20_dev", "rsi_14", "cv_50"]:
        assert feat in first_ind


def test_stocks_summary():
    """Kiểm tra endpoint /api/stocks/summary."""
    response = client.get("/api/stocks/summary?symbol=VIC")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "VIC"
    assert "latest_close" in data
    assert "change_pct" in data
    assert "volume" in data
    assert "rsi_14" in data


def test_stocks_board():
    """Kiểm tra endpoint /api/stocks/board."""
    response = client.get("/api/stocks/board")
    assert response.status_code == 200
    data = response.json()
    assert "indices" in data
    assert len(data["indices"]) >= 3
    assert "stocks" in data
    assert len(data["stocks"]) >= 5
    assert "breadth" in data
    assert "ai_market_insight" in data


def test_predict_signal_lightgbm():
    """Kiểm tra endpoint /api/predict/signal với mô hình LightGBM."""
    response = client.get("/api/predict/signal?symbol=VIC&model_type=lightgbm")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "VIC"
    assert data["model_type"].lower() == "lightgbm"
    assert data["predicted_label"] in [0, 1, 2]
    assert data["class_name"] in ["GIẢM", "ĐI NGANG", "TĂNG"]
    assert "probabilities" in data
    assert len(data["probabilities"]) == 3


def test_predict_batch():
    """Kiểm tra endpoint /api/predict/batch."""
    response = client.get("/api/predict/batch?model_type=lightgbm")
    assert response.status_code == 200
    data = response.json()
    assert data["total_symbols"] >= 5
    assert len(data["predictions"]) >= 5


def test_backtest_run():
    """Kiểm tra endpoint POST /api/backtest/run."""
    payload = {
        "symbol": "VIC",
        "model_type": "lightgbm",
        "initial_capital": 100_000_000.0,
        "slippage_rate": 0.0005,
    }
    response = client.post("/api/backtest/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "VIC"
    assert "metrics" in data
    assert "total_return_pct" in data["metrics"]
    assert "sharpe_ratio" in data["metrics"]
    assert "max_drawdown_pct" in data["metrics"]
    assert "equity_curve" in data
    assert len(data["equity_curve"]) > 0


def test_backtest_summary():
    """Kiểm tra endpoint GET /api/backtest/summary."""
    response = client.get("/api/backtest/summary?model_type=lightgbm")
    assert response.status_code == 200
    data = response.json()
    assert data["model_type"] == "LIGHTGBM"
    assert len(data["summary"]) >= 5


def test_invalid_symbol_or_model():
    """Kiểm tra xử lý lỗi khi nhập mã hoặc model không hợp lệ."""
    # Mã không tồn tại
    res_stock = client.get("/api/stocks/history?symbol=NON_EXISTENT_XYZ")
    assert res_stock.status_code == 404

    # Model không hỗ trợ
    res_model = client.get("/api/predict/signal?symbol=VIC&model_type=random_forest_xyz")
    assert res_model.status_code == 400


def test_predict_signal_post():
    """Kiểm tra endpoint POST /api/predict/signal."""
    payload = {"symbol": "VIC", "model_type": "lightgbm"}
    response = client.post("/api/predict/signal", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "VIC"
    assert "probabilities" in data


def test_predict_batch_post():
    """Kiểm tra endpoint POST /api/predict/batch."""
    payload = {"model_type": "lightgbm"}
    response = client.post("/api/predict/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_symbols"] >= 5


def test_invalid_symbol_backtest():
    """Kiểm tra backtest với mã không tồn tại hoặc model không hỗ trợ."""
    # Model không hợp lệ trả về 400
    payload_bad_model = {
        "symbol": "VIC",
        "model_type": "invalid_model_xyz",
        "initial_capital": 100_000_000.0,
    }
    res_bad_model = client.post("/api/backtest/run", json=payload_bad_model)
    assert res_bad_model.status_code == 400

    # Mã không tồn tại trả về 404
    payload_bad_sym = {
        "symbol": "NON_EXISTENT_XYZ",
        "model_type": "lightgbm",
        "initial_capital": 100_000_000.0,
    }
    res_bad_sym = client.post("/api/backtest/run", json=payload_bad_sym)
    assert res_bad_sym.status_code == 404


def test_stocks_sync_status():
    """Kiểm tra endpoint GET /api/stocks/sync-status."""
    response = client.get("/api/stocks/sync-status")
    assert response.status_code == 200
    data = response.json()
    assert "target_date" in data
    assert "session_type" in data
    assert "session_name" in data
    assert "status_label" in data
    assert "is_market_closed" in data
    assert "prediction_horizon_desc" in data


def test_predict_universal_symbol():
    """Kiểm tra dự đoán với mã mở rộng ngoài 5 mã mặc định (ví dụ VHM)."""
    response = client.get("/api/predict/signal?symbol=VHM&model_type=lightgbm")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "VHM"
    assert "probabilities" in data


def test_stocks_trigger_sync():
    """Kiểm tra endpoint POST /api/stocks/sync."""
    from unittest.mock import patch
    with patch("vn_stock.data_ingestion.sync_latest_market_data", return_value={"status": "completed"}):
        response = client.post("/api/stocks/sync")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "completed", "running"]


def test_predict_live_endpoints():
    """Kiểm tra endpoint /api/predict/live (GET & POST) với trajectory 3 phiên."""
    # Test GET
    res_get = client.get("/api/predict/live?symbol=VIC&model_type=lightgbm")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["symbol"] == "VIC"
    assert data_get["horizon"] == "T+3"
    assert data_get["horizon_days"] == 3
    assert data_get["is_live_synced"] is True
    assert "trajectory" in data_get
    assert len(data_get["trajectory"]) == 3
    assert data_get["trajectory"][0]["day_name"] == "T+1"
    assert data_get["trajectory"][1]["day_name"] == "T+2"
    assert data_get["trajectory"][2]["day_name"] == "T+3"

    # Test POST
    payload = {"symbol": "VIC", "model_type": "lightgbm"}
    res_post = client.post("/api/predict/live", json=payload)
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["is_live_synced"] is True
    assert len(data_post["trajectory"]) == 3


def test_stocks_sectors():
    """Kiểm tra endpoint GET /api/stocks/sectors."""
    res = client.get("/api/stocks/sectors")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "sector" in data[0]
    assert "symbols" in data[0]


def test_backtest_run_advanced_validation():
    """Kiểm tra ràng buộc dải ngày <= 1 năm của POST /api/backtest/run-advanced."""
    # Test dải ngày > 365 ngày -> Lỗi 400
    invalid_payload = {
        "scope_type": "stock",
        "symbol": "VIC",
        "start_date": "2023-01-01",
        "end_date": "2025-01-01",  # 2 năm > 365 ngày
        "initial_capital": 100_000_000,
        "model_type": "lightgbm",
    }
    res_err = client.post("/api/backtest/run-advanced", json=invalid_payload)
    assert res_err.status_code == 400
    assert "Khoảng thời gian chọn không quá 1 năm" in res_err.json()["detail"]

    # Test dải ngày hợp lệ (6 tháng)
    valid_payload = {
        "scope_type": "portfolio",
        "portfolio_symbols": ["VIC", "HPG"],
        "start_date": "2024-01-01",
        "end_date": "2024-06-30",
        "initial_capital": 100_000_000,
        "model_type": "lightgbm",
        "buy_conditions": {"use_ma": True},
        "sell_conditions": {"take_profit_pct": 0.15, "stop_loss_pct": 0.07},
    }
    res_ok = client.post("/api/backtest/run-advanced", json=valid_payload)
    assert res_ok.status_code == 200
    d = res_ok.json()
    assert d["scope_type"] == "portfolio"
    assert "aggregate_metrics" in d
    assert "portfolio_equity_curve" in d
    assert "symbols_breakdown" in d
    assert len(d["symbols_breakdown"]) >= 1
    assert "individual_results" in d
    for sym, ind in d["individual_results"].items():
        assert "equity_curve" in ind
        if len(ind["equity_curve"]) > 0:
            first_pt = ind["equity_curve"][0]
            assert "date" in first_pt
            assert "total_equity" in first_pt
            assert "benchmark_equity" in first_pt
            assert "drawdown_pct" in first_pt
            assert "daily_return" in first_pt


def test_backtest_presets_endpoint():
    """Kiểm tra endpoint GET /api/backtest/presets."""
    response = client.get("/api/backtest/presets")
    assert response.status_code == 200
    data = response.json()
    assert "presets" in data
    assert len(data["presets"]) >= 8
    first = data["presets"][0]
    assert "id" in first
    assert "name" in first
    assert "category" in first


def test_backtest_signals_recent_endpoint():
    """Kiểm tra endpoint GET /api/backtest/signals/recent."""
    response = client.get("/api/backtest/signals/recent")
    assert response.status_code == 200
    data = response.json()
    assert "signals" in data
    assert isinstance(data["signals"], list)


def test_predict_retrain_endpoint():
    """Kiểm tra endpoint POST /api/predict/retrain với mock training engine."""
    from unittest.mock import patch
    mock_ret = {
        "status": "success",
        "horizon": "T+3",
        "lightgbm_metrics": {"accuracy": 0.65},
        "lstm_metrics": {"accuracy": 0.62},
    }
    with patch("vn_stock.modeling.train.train_production_model", return_value=mock_ret):
        payload = {
            "horizon": 3,
            "threshold": 0.02,
            "val_buffer_days": 40,
            "scope": "VN30",
        }
        response = client.post("/api/predict/retrain", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["horizon"] == "T+3"


def test_backtest_run_advanced_index_scope_endpoint():
    """Kiểm tra endpoint POST /api/backtest/run-advanced với scope = index."""
    payload = {
        "scope_type": "index",
        "index_name": "VN30",
        "start_date": "2024-01-01",
        "end_date": "2024-04-01",
    }
    response = client.post("/api/backtest/run-advanced", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scope_type"] == "index"
    assert "VN30" in data["scope_target"]
    assert len(data["symbols_breakdown"]) >= 1


def test_backtest_run_advanced_stock_scope_endpoint():
    """Kiểm tra endpoint POST /api/backtest/run-advanced với scope = stock."""
    payload = {
        "scope_type": "stock",
        "symbol": "VIC",
        "start_date": "2024-01-01",
        "end_date": "2024-04-01",
    }
    response = client.post("/api/backtest/run-advanced", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scope_type"] == "stock"
    assert data["scope_target"] == "VIC"



