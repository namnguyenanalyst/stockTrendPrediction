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
    """Kiểm tra backtest với mã không thuộc core symbols trả về 400."""
    payload = {
        "symbol": "SSI",
        "model_type": "lightgbm",
        "initial_capital": 100_000_000.0,
    }
    response = client.post("/api/backtest/run", json=payload)
    assert response.status_code == 400


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

