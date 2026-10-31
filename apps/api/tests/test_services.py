"""Kiểm thử chuyên sâu cho tầng Services và Logic phụ trợ của VN Stock FastAPI Backend."""

import asyncio
import os
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi import HTTPException

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from app.main import app, lifespan, run_startup_sync
from app.models.schemas import (
    AdvancedBacktestRequest,
    BacktestConditionFilter,
    BacktestScopeType,
    PredictionResponse,
)
from app.services import backtest_service, prediction_service, stock_service

# ---------------------------------------------------------------------------
# BACKTEST SERVICE TESTS
# ---------------------------------------------------------------------------


def test_get_presets_service_success():
    """Kiểm tra get_presets_service trả về đủ danh sách 8 chiến thuật mẫu."""
    res = backtest_service.get_presets_service()
    assert len(res.presets) >= 8
    first = res.presets[0]
    assert first.id
    assert first.name
    assert first.category
    assert first.cumulative_pnl_pct is not None
    assert first.win_rate_pct is not None


def test_get_presets_service_exception_raises_http_500():
    """Kiểm tra get_presets_service ném HTTPException 500 khi vn_stock ném lỗi."""
    with patch("vn_stock.backtest.get_strategy_presets", side_effect=RuntimeError("DB error")):
        with pytest.raises(HTTPException) as exc_info:
            backtest_service.get_presets_service()
        assert exc_info.value.status_code == 500
        assert "Không thể tải danh sách chiến thuật mẫu" in exc_info.value.detail


def test_get_recent_signals_service_success():
    """Kiểm tra get_recent_signals_service trả về danh sách tín hiệu giao dịch."""
    res = backtest_service.get_recent_signals_service()
    assert isinstance(res.signals, list)
    if res.signals:
        sig = res.signals[0]
        assert sig.symbol
        assert sig.action in ["BUY", "SELL", "HOLD"]
        assert sig.price >= 0


def test_get_recent_signals_service_exception_raises_http_500():
    """Kiểm tra get_recent_signals_service ném HTTPException 500 khi gặp lỗi."""
    with patch("vn_stock.backtest.get_recent_strategy_signals", side_effect=RuntimeError("Signals error")):
        with pytest.raises(HTTPException) as exc_info:
            backtest_service.get_recent_signals_service()
        assert exc_info.value.status_code == 500
        assert "Không thể tải danh sách tín hiệu mới" in exc_info.value.detail


def test_run_advanced_backtest_start_date_after_end_date_raises_http_400():
    """Kiểm tra lỗi 400 khi start_date lớn hơn end_date."""
    req = AdvancedBacktestRequest(
        scope_type=BacktestScopeType.STOCK,
        symbol="VIC",
        start_date="2024-06-01",
        end_date="2024-01-01",
    )
    with pytest.raises(HTTPException) as exc_info:
        backtest_service.run_advanced_backtest(req)
    assert exc_info.value.status_code == 400
    assert "Ngày bắt đầu không được lớn hơn ngày kết thúc" in exc_info.value.detail


def test_run_advanced_backtest_scope_stock_success():
    """Kiểm tra run_advanced_backtest với scope_type = STOCK."""
    req = AdvancedBacktestRequest(
        scope_type=BacktestScopeType.STOCK,
        symbol="VIC",
        start_date="2024-01-01",
        end_date="2024-06-01",
        buy_conditions=BacktestConditionFilter(use_ma=True),
        sell_conditions=BacktestConditionFilter(take_profit_pct=0.10, stop_loss_pct=0.05),
    )
    res = backtest_service.run_advanced_backtest(req)
    assert res.scope_type == "stock"
    assert res.scope_target == "VIC"
    assert res.symbols_count == 1
    assert res.aggregate_metrics.total_return_pct is not None


def test_run_advanced_backtest_scope_index_vn30_success():
    """Kiểm tra run_advanced_backtest với scope_type = INDEX (VN30)."""
    req = AdvancedBacktestRequest(
        scope_type=BacktestScopeType.INDEX,
        index_name="VN30",
        start_date="2024-01-01",
        end_date="2024-04-01",
        buy_conditions=BacktestConditionFilter(use_rsi=True),
    )
    res = backtest_service.run_advanced_backtest(req)
    assert res.scope_type == "index"
    assert "VN30" in res.scope_target
    assert res.symbols_count >= 1


def test_run_advanced_backtest_scope_sector_success():
    """Kiểm tra run_advanced_backtest với scope_type = SECTOR (Bất động sản)."""
    req = AdvancedBacktestRequest(
        scope_type=BacktestScopeType.SECTOR,
        sector_name="Bất động sản",
        start_date="2024-01-01",
        end_date="2024-04-01",
    )
    res = backtest_service.run_advanced_backtest(req)
    assert res.scope_type == "sector"
    assert "Bất động sản" in res.scope_target
    assert res.symbols_count >= 1


def test_run_advanced_backtest_unknown_sector_fallback_default_symbols():
    """Kiểm tra run_advanced_backtest khi tên ngành không tồn tại -> fallback danh sách mặc định."""
    req = AdvancedBacktestRequest(
        scope_type=BacktestScopeType.SECTOR,
        sector_name="Ngành Không Tồn Tại XYZ",
        start_date="2024-01-01",
        end_date="2024-04-01",
    )
    res = backtest_service.run_advanced_backtest(req)
    assert res.scope_type == "sector"
    assert res.symbols_count >= 1


def test_run_advanced_backtest_engine_failure_raises_http_500():
    """Kiểm tra run_advanced_backtest ném 500 khi engine mô phỏng gặp ngoại lệ bất ngờ."""
    req = AdvancedBacktestRequest(
        scope_type=BacktestScopeType.STOCK,
        symbol="VIC",
        start_date="2024-01-01",
        end_date="2024-06-01",
    )
    with patch("vn_stock.backtest.run_portfolio_backtest", side_effect=RuntimeError("Simulation crash")):
        with pytest.raises(HTTPException) as exc_info:
            backtest_service.run_advanced_backtest(req)
        assert exc_info.value.status_code == 500
        assert "Lỗi khi thực thi kiểm thử chiến lược" in exc_info.value.detail


# ---------------------------------------------------------------------------
# PREDICTION SERVICE TESTS
# ---------------------------------------------------------------------------


def test_retrain_production_system_success():
    """Kiểm tra retrain_production_system gọi thành công mô hình huấn luyện."""
    mock_summary = {
        "status": "success",
        "horizon": "T+3",
        "lightgbm_metrics": {"accuracy": 0.65},
        "lstm_metrics": {"accuracy": 0.62},
    }
    with patch("vn_stock.modeling.train.train_production_model", return_value=mock_summary):
        res = prediction_service.retrain_production_system(
            horizon=3,
            threshold=0.02,
            val_buffer_days=40,
            scope="VN30",
        )
        assert res["status"] == "success"
        assert res["horizon"] == "T+3"


def test_retrain_production_system_exception_raises_http_500():
    """Kiểm tra retrain_production_system ném HTTPException 500 khi lỗi huấn luyện."""
    with patch("vn_stock.modeling.train.train_production_model", side_effect=RuntimeError("OOM error")):
        with pytest.raises(HTTPException) as exc_info:
            prediction_service.retrain_production_system()
        assert exc_info.value.status_code == 500
        assert "Lỗi khi huấn luyện lại mô hình thực chiến" in exc_info.value.detail


def test_get_market_sync_status_exception_returns_unknown_dict():
    """Kiểm tra get_market_sync_status bắt ngoại lệ và trả về dictionary error."""
    with patch("vn_stock.market_session.get_target_market_session_info", side_effect=RuntimeError("Session failed")):
        res = prediction_service.get_market_sync_status()
        assert res["status"] == "unknown"
        assert "Session failed" in res["error"]


def test_trigger_market_sync_exception_raises_http_500():
    """Kiểm tra trigger_market_sync ném HTTPException 500 khi gặp sự cố đồng bộ."""
    with patch("vn_stock.data_ingestion.sync_latest_market_data", side_effect=RuntimeError("Network down")):
        with pytest.raises(HTTPException) as exc_info:
            prediction_service.trigger_market_sync(force=True)
        assert exc_info.value.status_code == 500
        assert "Lỗi khi đồng bộ dữ liệu" in exc_info.value.detail


def test_predict_batch_signals_resilient_to_individual_symbol_failure():
    """Kiểm tra predict_batch_signals vẫn hoàn thành và bỏ qua mã bị lỗi."""
    with patch("app.services.prediction_service.predict_stock_signal") as mock_pred:
        def side_effect(symbol, model_type):
            if symbol == "HPG":
                raise ValueError("HPG data corrupted")
            return PredictionResponse(
                symbol=symbol,
                date="2026-10-24",
                current_price=50.0,
                predicted_label=1,
                class_name="ĐI NGANG",
                signal="NẮM GIỮ (HOLD)",
                probabilities={"GIẢM": 0.2, "ĐI NGANG": 0.6, "TĂNG": 0.2},
                model_type="lightgbm",
            )

        mock_pred.side_effect = side_effect
        res = prediction_service.predict_batch_signals(model_type="lightgbm")
        assert res.total_symbols >= 4
        symbols = [p.symbol for p in res.predictions]
        assert "HPG" not in symbols


# ---------------------------------------------------------------------------
# STOCK SERVICE TESTS
# ---------------------------------------------------------------------------


def test_get_index_constituents_vn30_and_vn100():
    """Kiểm tra hàm get_index_constituents với các rổ chỉ số khác nhau."""
    vni = stock_service.get_index_constituents("VNINDEX")
    assert isinstance(vni, list)
    assert len(vni) >= 5

    vn100 = stock_service.get_index_constituents("VN100")
    assert isinstance(vn100, list)
    assert len(vn100) >= 5

    fallback = stock_service.get_index_constituents("UNKNOWN_INDEX")
    assert isinstance(fallback, list)
    assert len(fallback) >= 5


def test_compute_fallback_indicators():
    """Kiểm tra _compute_fallback_indicators tính đúng các cột kỹ thuật khi thư viện chính không khả dụng."""
    dates = pd.date_range("2023-01-01", periods=250, freq="D")
    df = pd.DataFrame({
        "Date": dates,
        "Open": [100.0 + i * 0.1 for i in range(250)],
        "High": [102.0 + i * 0.1 for i in range(250)],
        "Low": [99.0 + i * 0.1 for i in range(250)],
        "Close": [101.0 + i * 0.1 for i in range(250)],
        "Volume": [1_000_000] * 250,
    })
    feat_df = stock_service._compute_fallback_indicators(df)
    assert "SMA_20_Dev" in feat_df.columns
    assert "RSI" in feat_df.columns
    assert "CV_50" in feat_df.columns
    assert len(feat_df) > 0


def test_load_stock_dataframe_synthetic_fallback(tmp_path):
    """Kiểm tra load_stock_dataframe nạp fallback từ VNINDEX khi mã thuộc VN30 nhưng chưa có file nến riêng."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    df_vni = pd.DataFrame({
        "Date": dates,
        "Close": [1200.0] * 10,
        "Open": [1195.0] * 10,
        "High": [1205.0] * 10,
        "Low": [1190.0] * 10,
        "Volume": [500_000_000] * 10,
    })
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True)
    vni_file = raw_dir / "VNINDEX.parquet"
    df_vni.to_parquet(vni_file)

    with patch("app.services.stock_service.settings.DATA_DIR", tmp_path):
        # Chọn mã SSI có trong stock_factors
        df_ssi = stock_service.load_stock_dataframe("SSI", allow_remote_fetch=False)
        assert df_ssi is not None
        assert not df_ssi.empty
        assert "Close" in df_ssi.columns
        assert df_ssi["Symbol"].iloc[0] == "SSI"


# ---------------------------------------------------------------------------
# MAIN LIFESPAN & STARTUP SYNC TESTS
# ---------------------------------------------------------------------------


def test_run_startup_sync_handles_exception_cleanly():
    """Kiểm tra run_startup_sync không crash ứng dụng khi tiến trình sync ném ngoại lệ."""
    async def _run():
        with patch("vn_stock.data_ingestion.sync_latest_market_data", side_effect=RuntimeError("Sync error")):
            await run_startup_sync()

    asyncio.run(_run())


def test_app_lifespan_context():
    """Kiểm tra lifespan context manager khởi động và kết thúc sạch sẽ."""
    async def _run():
        with patch("app.main.settings.AUTO_SYNC_ON_STARTUP", False):
            async with lifespan(app):
                pass

    asyncio.run(_run())
