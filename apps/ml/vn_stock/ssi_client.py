"""Client kết nối dịch vụ SSI Fast Connect Data (FC-Data) để thu thập dữ liệu chứng khoán chuyên nghiệp."""

from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import pandas as pd
import requests

from vn_stock.config import MONOREPO_ROOT, PROJ_ROOT

# Tự động nạp cấu hình từ .env ở root repo hoặc apps/ml hoặc cwd
for env_path in [
    MONOREPO_ROOT / ".env",
    PROJ_ROOT / ".env",
    Path.cwd() / ".env",
    Path(__file__).resolve().parents[3] / ".env",
]:
    if env_path.exists():
        load_dotenv(env_path)


class SSIFastConnectClient:
    """Client giao tiếp với SSI Fast Connect Market Data API."""

    def __init__(
        self,
        consumer_id: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        self.consumer_id = consumer_id or os.getenv("SSI_CONSUMER_ID", "")
        self.consumer_secret = consumer_secret or os.getenv("SSI_CONSUMER_SECRET", "")
        self.api_url = (api_url or os.getenv("SSI_API_URL", "https://fc-data.ssi.com.vn/")).rstrip("/") + "/"

        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._session = requests.Session()
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_access_token(self) -> str:
        """Lấy JWT Access Token từ SSI hoặc tái sử dụng token đã cache nếu còn hạn."""
        now = datetime.now()
        if (
            self._access_token is not None
            and self._token_expiry is not None
            and now < self._token_expiry
        ):
            return self._access_token

        if not self.consumer_id or not self.consumer_secret:
            raise ValueError(
                "Chưa cấu hình SSI_CONSUMER_ID hoặc SSI_CONSUMER_SECRET trong file .env."
            )

        url = self.api_url + "api/v2/Market/AccessToken"
        payload = {
            "consumerID": self.consumer_id,
            "consumerSecret": self.consumer_secret,
        }

        response = self._session.post(url, json=payload, headers=self._headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 200 or "data" not in data:
            raise RuntimeError(f"Lỗi xác thực SSI FC-Data: {data.get('message')}")

        self._access_token = data["data"]["accessToken"]
        # Token của SSI thường có thời hạn 8-24 tiếng, an toàn cache trong 6 tiếng
        self._token_expiry = now + timedelta(hours=6)
        return self._access_token

    def _format_date_for_ssi(self, date_str: str) -> str:
        """Chuyển định dạng YYYY-MM-DD sang DD/MM/YYYY theo chuẩn SSI API."""
        try:
            # Nếu đã là định dạng DD/MM/YYYY
            if "/" in date_str:
                return date_str
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except Exception:
            return date_str

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: str = "2020-01-01",
        end_date: Optional[str] = None,
        unit: str = "kVND",  # "kVND" (chia 1000 để tương thích dự án cũ) hoặc "VND"
    ) -> pd.DataFrame:
        """
        Truy vấn nến lịch sử ngày (Daily OHLCV) có hỗ trợ phân trang tự động.
        
        Args:
            symbol: Mã cổ phiếu (VIC, FPT, HPG, ...)
            start_date: Ngày bắt đầu (YYYY-MM-DD hoặc DD/MM/YYYY)
            end_date: Ngày kết thúc (mặc định là ngày hiện tại)
            unit: 'kVND' (nghìn đồng - chia 1000) hoặc 'VND' (đồng nguyên giá)
        """
        token = self._get_access_token()
        headers = {
            **self._headers,
            "Authorization": f"Bearer {token}",
        }

        from_date_ssi = self._format_date_for_ssi(start_date)
        if end_date is None:
            to_date_ssi = datetime.now().strftime("%d/%m/%Y")
        else:
            to_date_ssi = self._format_date_for_ssi(end_date)

        all_records: List[Dict[str, Any]] = []
        page_index = 1
        page_size = 1000

        while True:
            params = {
                "symbol": symbol.upper(),
                "fromDate": from_date_ssi,
                "toDate": to_date_ssi,
                "pageIndex": page_index,
                "pageSize": page_size,
                "ascending": True,
            }

            url = self.api_url + "api/v2/Market/DailyOhlc"
            res = self._session.get(url, params=params, headers=headers, timeout=20)
            res.raise_for_status()
            res_data = res.json()

            status_str = str(res_data.get("status", "")).lower()
            if status_str not in ["200", "success"]:
                raise RuntimeError(f"Lỗi truy vấn DailyOhlc {symbol}: {res_data.get('message')}")

            data_batch = res_data.get("data", [])
            if not data_batch:
                break

            all_records.extend(data_batch)

            total_record = res_data.get("totalRecord", 0)
            if len(all_records) >= total_record or len(data_batch) < page_size:
                break

            page_index += 1

        if not all_records:
            return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])

        df = pd.DataFrame(all_records)

        # Chuẩn hóa cột
        df["Date"] = pd.to_datetime(df["TradingDate"], format="%d/%m/%Y")
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Quy đổi đơn vị giá nếu cần (mặc định kVND để đồng bộ với VN_Stock)
        if unit == "kVND":
            price_cols = ["Open", "High", "Low", "Close"]
            for col in price_cols:
                if col in df.columns:
                    df[col] = df[col] / 1000.0

        # Sắp xếp theo ngày tăng dần
        df = df.sort_values("Date").reset_index(drop=True)

        return df[["Date", "Open", "High", "Low", "Close", "Volume"]]

    def get_index_components(self, index_code: str = "VN30") -> List[str]:
        """Lấy danh sách các mã cổ phiếu trong rổ chỉ số (VN30, VN100, ...)."""
        token = self._get_access_token()
        headers = {
            **self._headers,
            "Authorization": f"Bearer {token}",
        }
        url = self.api_url + "api/v2/Market/IndexComponents"
        params = {"indexCode": index_code.upper(), "pageIndex": 1, "pageSize": 100}

        res = self._session.get(url, params=params, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()

        status_str = str(data.get("status", "")).lower()
        if status_str not in ["200", "success"]:
            raise RuntimeError(f"Lỗi lấy rổ chỉ số {index_code}: {data.get('message')}")

        result_symbols: List[str] = []
        data_list = data.get("data", [])
        if isinstance(data_list, list):
            for index_group in data_list:
                components = index_group.get("IndexComponent", [])
                for comp in components:
                    symbol = comp.get("StockSymbol") or comp.get("Isin")
                    if symbol and symbol not in result_symbols:
                        result_symbols.append(symbol)

        return result_symbols
