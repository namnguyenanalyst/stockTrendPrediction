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
