"""Kiểm thử cho SSI Fast Connect Client."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from vn_stock.ssi_client import SSIFastConnectClient


def test_ssi_client_date_formatting():
    client = SSIFastConnectClient(consumer_id="mock_id", consumer_secret="mock_secret")
    assert client._format_date_for_ssi("2024-01-15") == "15/01/2024"
    assert client._format_date_for_ssi("15/01/2024") == "15/01/2024"


def test_ssi_client_parsing_ohlcv():
    client = SSIFastConnectClient(consumer_id="mock_id", consumer_secret="mock_secret")
    client._get_access_token = MagicMock(return_value="mock_token")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "Success",
        "message": "Success",
        "totalRecord": 2,
        "data": [
            {
                "Symbol": "VIC",
                "TradingDate": "02/01/2024",
                "Open": "22000",
                "High": "22500",
                "Low": "21800",
                "Close": "22100",
                "Volume": "1500000",
            },
            {
                "Symbol": "VIC",
                "TradingDate": "03/01/2024",
                "Open": "22100",
                "High": "22300",
                "Low": "21900",
                "Close": "22200",
                "Volume": "1200000",
            },
        ],
    }
    client._session.get = MagicMock(return_value=mock_response)

    df = client.get_daily_ohlcv("VIC", start_date="2024-01-01", end_date="2024-01-05", unit="kVND")

    assert len(df) == 2
    assert "Date" in df.columns
    assert "Close" in df.columns
    # Kiểm tra quy đổi sang kVND (22100 / 1000 = 22.1)
    assert pytest.approx(df.iloc[0]["Close"]) == 22.1
    assert pytest.approx(df.iloc[1]["Close"]) == 22.2
    assert df.iloc[0]["Volume"] == 1500000


def test_ssi_client_parsing_daily_index():
    client = SSIFastConnectClient(consumer_id="mock_id", consumer_secret="mock_secret")
    client._get_access_token = MagicMock(return_value="mock_token")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "Success",
        "message": "Success",
        "data": [
            {
                "IndexId": "VNINDEX",
                "TradingDate": "02/01/2024",
                "IndexValue": "1131.72",
            },
            {
                "IndexId": "VNINDEX",
                "TradingDate": "03/01/2024",
                "IndexValue": "1144.17",
            },
        ],
    }
    client._session.get = MagicMock(return_value=mock_response)

    with patch("time.sleep", return_value=None):
        df = client.get_daily_index("VNINDEX", start_date="2024-01-01", end_date="2024-01-05", chunk_days=25)

    assert len(df) == 2
    assert "Date" in df.columns
    assert "VNINDEX_Close" in df.columns
    assert pytest.approx(df.iloc[0]["VNINDEX_Close"]) == 1131.72
    assert pytest.approx(df.iloc[1]["VNINDEX_Close"]) == 1144.17


def test_ssi_client_daily_index_empty_chunk_success():
    """Kiểm tra khi chunk trả về status Success nhưng data rỗng (nghỉ lễ), hàm coi là thành công."""
    client = SSIFastConnectClient(consumer_id="mock_id", consumer_secret="mock_secret")
    client._get_access_token = MagicMock(return_value="mock_token")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "Success",
        "message": "Success",
        "data": [],
    }
    client._session.get = MagicMock(return_value=mock_response)

    with patch("time.sleep", return_value=None):
        df = client.get_daily_index("VNINDEX", start_date="2024-02-08", end_date="2024-02-14", chunk_days=25)

    assert df.empty
    assert "Date" in df.columns
    assert "VNINDEX_Close" in df.columns


def test_ssi_client_get_access_token_cached():
    """Kiểm tra tái sử dụng access token hợp lệ còn trong hạn."""
    from datetime import datetime, timedelta

    client = SSIFastConnectClient(consumer_id="id", consumer_secret="secret")
    client._access_token = "valid_cached_token"
    client._token_expiry = datetime.now() + timedelta(hours=2)

    # Không được gọi API qua session
    client._session.post = MagicMock()
    token = client._get_access_token()
    assert token == "valid_cached_token"
    client._session.post.assert_not_called()


def test_ssi_client_get_access_token_missing_credentials():
    """Kiểm tra báo lỗi ValueError khi chưa cấu hình Consumer ID hoặc Secret."""
    client = SSIFastConnectClient(consumer_id="temp", consumer_secret="temp")
    client.consumer_id = ""
    client.consumer_secret = ""
    with pytest.raises(ValueError, match="Chưa cấu hình SSI_CONSUMER_ID"):
        client._get_access_token()


def test_ssi_client_get_access_token_success():
    """Kiểm tra lấy token thành công khi chưa có cache."""
    client = SSIFastConnectClient(consumer_id="id", consumer_secret="secret")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "status": 200,
        "data": {"accessToken": "new_jwt_token_123"},
    }
    client._session.post = MagicMock(return_value=mock_resp)

    token = client._get_access_token()
    assert token == "new_jwt_token_123"
    assert client._access_token == "new_jwt_token_123"
    assert client._token_expiry is not None


def test_ssi_client_get_access_token_retry_and_fail():
    """Kiểm tra thử lại 3 lần thất bại sẽ ném ngoại lệ RuntimeError."""
    client = SSIFastConnectClient(consumer_id="id", consumer_secret="secret")
    client._session.post = MagicMock(side_effect=Exception("Connection refused"))

    with patch("time.sleep", return_value=None):
        with pytest.raises(RuntimeError, match="Không thể lấy JWT Access Token"):
            client._get_access_token()
    assert client._session.post.call_count == 3


def test_ssi_client_date_formatting_invalid_fallback():
    """Kiểm tra khi chuỗi ngày sai định dạng thì trả về chính chuỗi đó."""
    client = SSIFastConnectClient(consumer_id="id", consumer_secret="secret")
    assert client._format_date_for_ssi("invalid_date_string") == "invalid_date_string"


def test_ssi_client_get_daily_ohlcv_pagination():
    """Kiểm tra cơ chế phân trang khi tổng số bản ghi vượt quá kích thước 1 trang (1000 bản ghi)."""
    client = SSIFastConnectClient(consumer_id="mock_id", consumer_secret="mock_secret")
    client._get_access_token = MagicMock(return_value="mock_token")

    # Tạo 1000 ngày hợp lệ cho page 1
    dates = pd.date_range("2021-01-01", periods=1000, freq="D")
    rec_p1 = [
        {"Symbol": "VIC", "TradingDate": d.strftime("%d/%m/%Y"), "Open": "20000", "High": "21000", "Low": "19000", "Close": "20500", "Volume": "100000"}
        for d in dates
    ]
    rec_p2 = [
        {"Symbol": "VIC", "TradingDate": "15/10/2024", "Open": "21000", "High": "22000", "Low": "20000", "Close": "21500", "Volume": "120000"}
    ]

    resp1 = MagicMock()
    resp1.json.return_value = {"status": "Success", "totalRecord": 1001, "data": rec_p1}
    resp2 = MagicMock()
    resp2.json.return_value = {"status": "Success", "totalRecord": 1001, "data": rec_p2}

    client._session.get = MagicMock(side_effect=[resp1, resp2])

    with patch("time.sleep", return_value=None):
        df = client.get_daily_ohlcv("VIC", start_date="2021-01-01", end_date="2024-10-15")

    assert len(df) == 1001
    assert client._session.get.call_count == 2



def test_ssi_client_get_index_components():
    """Kiểm tra phương thức lấy danh sách mã thành phần của rổ chỉ số VN30."""
    client = SSIFastConnectClient(consumer_id="mock_id", consumer_secret="mock_secret")
    client._get_access_token = MagicMock(return_value="mock_token")

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "status": "200",
        "data": [
            {
                "IndexComponent": [
                    {"StockSymbol": "VIC"},
                    {"StockSymbol": "HPG"},
                    {"StockSymbol": "FPT"},
                ]
            }
        ],
    }
    client._session.get = MagicMock(return_value=mock_resp)

    components = client.get_index_components("VN30")
    assert components == ["VIC", "HPG", "FPT"]


def test_ssi_client_get_index_components_error():
    """Kiểm tra báo lỗi khi API lấy rổ chỉ số trả về status thất bại."""
    client = SSIFastConnectClient(consumer_id="mock_id", consumer_secret="mock_secret")
    client._get_access_token = MagicMock(return_value="mock_token")

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "500", "message": "Index not found"}
    client._session.get = MagicMock(return_value=mock_resp)

    with pytest.raises(RuntimeError, match="Lỗi lấy rổ chỉ số"):
        client.get_index_components("INVALID_INDEX")


def test_ssi_client_daily_index_chunk_failure_raises_runtime_error():
    """Kiểm tra khi 1 chunk thất bại cả 3 lần thử thì ném ngoại lệ RuntimeError."""
    client = SSIFastConnectClient(consumer_id="mock_id", consumer_secret="mock_secret")
    client._get_access_token = MagicMock(return_value="mock_token")

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    client._session.get = MagicMock(return_value=mock_resp)

    with patch("time.sleep", return_value=None):
        with pytest.raises(RuntimeError, match="Truy vấn VNINDEX thất bại sau 3 lần thử"):
            client.get_daily_index("VNINDEX", start_date="2024-01-01", end_date="2024-01-05")


