"""Kiểm thử tự động cho Autonomous Retrain Worker (infra/scripts/retrain_worker.py)."""

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKER_SCRIPT = REPO_ROOT / "infra" / "scripts" / "retrain_worker.py"

spec = importlib.util.spec_from_file_location("retrain_worker", WORKER_SCRIPT)
retrain_worker = importlib.util.module_from_spec(spec)
sys.modules["retrain_worker"] = retrain_worker
spec.loader.exec_module(retrain_worker)

ICT = retrain_worker.ICT
is_scheduled_time = retrain_worker.is_scheduled_time
trigger_retrain = retrain_worker.trigger_retrain


def test_is_scheduled_time_logic():
    """Kiểm tra logic phát hiện thời điểm kích hoạt Chủ Nhật 02:00 ICT."""
    # 1. Đúng thời điểm: Chủ Nhật 02:05 ICT (2026-11-08 là Chủ Nhật)
    dt_sunday_0205 = datetime(2026, 11, 8, 2, 5, tzinfo=ICT)
    assert is_scheduled_time(dt_sunday_0205, last_run_date=None) is True

    # 2. Đã chạy hôm nay -> Không chạy lặp lại
    assert is_scheduled_time(dt_sunday_0205, last_run_date="2026-11-08") is False

    # 3. Sai ngày: Thứ Hai (2026-11-09) lúc 02:05 ICT
    dt_monday_0205 = datetime(2026, 11, 9, 2, 5, tzinfo=ICT)
    assert is_scheduled_time(dt_monday_0205, last_run_date=None) is False

    # 4. Sai giờ: Chủ Nhật lúc 03:00 ICT
    dt_sunday_0300 = datetime(2026, 11, 8, 3, 0, tzinfo=ICT)
    assert is_scheduled_time(dt_sunday_0300, last_run_date=None) is False


def test_trigger_retrain_requires_secret():
    """trigger_retrain phải từ chối khi thiếu secret."""
    with pytest.raises(ValueError, match="INTERNAL_WORKER_SECRET không được để trống"):
        trigger_retrain(api_base_url="http://localhost:8000", secret="")


def test_trigger_retrain_success():
    """trigger_retrain gửi đúng payload và header X-Internal-Worker-Secret."""
    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.read.return_value = json.dumps({"status": "success", "message": "Retrained"}).encode("utf-8")
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        res = trigger_retrain(
            api_base_url="http://vn_stock_api:8000",
            secret="my_super_secret_token",
            scope="VN30",
            horizon=3,
        )

        assert res["status"] == "success"
        assert mock_urlopen.call_count == 1

        req = mock_urlopen.call_args[0][0]
        assert req.get_header("X-internal-worker-secret") == "my_super_secret_token"
        assert req.get_header("Content-type") == "application/json"
        assert req.full_url == "http://vn_stock_api:8000/api/v1/predict/retrain"

        payload = json.loads(req.data.decode("utf-8"))
        assert payload["scope"] == "VN30"
        assert payload["horizon"] == 3
