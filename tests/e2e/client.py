import os
from typing import Any, Dict, Optional
import httpx
from fastapi.testclient import TestClient


class E2EClient:
    """Opaque-box HTTP Client for exercising Backend REST API endpoints.

    Supports both live remote execution (via HTTP base_url) and
    in-process execution (via fastapi.testclient.TestClient).
    Maintains session state including Bearer access tokens and HTTP cookie jar.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        app: Optional[Any] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.access_token: Optional[str] = None
        self.stored_cookies: Dict[str, str] = {}

        if app is not None:
            self._raw_client = TestClient(
                app=app,
                base_url=self.base_url or "http://testserver",
                follow_redirects=True,
            )
        else:
            self._raw_client = httpx.Client(
                base_url=self.base_url,
                timeout=30.0,
                follow_redirects=True,
            )

    def set_token(self, token: Optional[str]) -> None:
        """Explicitly set or clear the Bearer Access Token."""
        self.access_token = token

    def clear_token(self) -> None:
        """Clear the current access token."""
        self.access_token = None

    def set_cookie(self, key: str, value: str) -> None:
        """Manually set a cookie in the client session."""
        self.stored_cookies[key] = value

    def clear_cookies(self) -> None:
        """Clear all stored cookies."""
        self.stored_cookies.clear()

    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        req_headers = dict(headers or {})
        if self.access_token and "Authorization" not in req_headers and "authorization" not in req_headers:
            req_headers["Authorization"] = f"Bearer {self.access_token}"
        return req_headers

    def _prepare_cookies(self, cookies: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        merged_cookies = dict(self.stored_cookies)
        if cookies:
            merged_cookies.update(cookies)
        return merged_cookies

    def _capture_cookies_from_response(self, response: httpx.Response) -> None:
        for name, value in response.cookies.items():
            self.stored_cookies[name] = value

    def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """Send an arbitrary HTTP request maintaining auth and cookies."""
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        final_headers = self._prepare_headers(headers)
        final_cookies = self._prepare_cookies(cookies)

        response = self._raw_client.request(
            method=method,
            url=url,
            headers=final_headers,
            cookies=final_cookies,
            **kwargs,
        )
        self._capture_cookies_from_response(response)
        return response

    def get(self, path: str, **kwargs) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> httpx.Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)

    # -------------------------------------------------------------------------
    # High-level REST API Contract Helpers
    # -------------------------------------------------------------------------

    def register(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        risk_profile: Optional[str] = None,
    ) -> httpx.Response:
        payload: Dict[str, Any] = {"email": email, "password": password}
        if full_name is not None:
            payload["full_name"] = full_name
        if risk_profile is not None:
            payload["risk_profile"] = risk_profile
        return self.post("/api/v1/auth/register", json=payload)

    def login(self, email: str, password: str) -> httpx.Response:
        payload = {"email": email, "password": password}
        res = self.post("/api/v1/auth/login", json=payload)
        if res.status_code == 200:
            data = res.json()
            token = data.get("access_token")
            if token:
                self.set_token(token)
        return res

    def refresh(self, refresh_token: Optional[str] = None) -> httpx.Response:
        payload = {"refresh_token": refresh_token} if refresh_token else {}
        res = self.post("/api/v1/auth/refresh", json=payload)
        if res.status_code == 200:
            data = res.json()
            token = data.get("access_token")
            if token:
                self.set_token(token)
        return res

    def me(self) -> httpx.Response:
        return self.get("/api/v1/auth/me")

    def list_watchlists(self) -> httpx.Response:
        return self.get("/api/v1/user/watchlists")

    def create_watchlist(self, name: str, symbols: list) -> httpx.Response:
        payload = {"name": name, "symbols": symbols}
        return self.post("/api/v1/user/watchlists", json=payload)

    def delete_watchlist(self, watchlist_id: str) -> httpx.Response:
        return self.delete(f"/api/v1/user/watchlists/{watchlist_id}")

    def list_presets(self) -> httpx.Response:
        return self.get("/api/v1/user/presets")

    def create_preset(
        self,
        name: str,
        parameters: Dict[str, Any],
        description: Optional[str] = None,
    ) -> httpx.Response:
        payload: Dict[str, Any] = {"name": name, "parameters": parameters}
        if description is not None:
            payload["description"] = description
        return self.post("/api/v1/user/presets", json=payload)

    def delete_preset(self, preset_id: str) -> httpx.Response:
        return self.delete(f"/api/v1/user/presets/{preset_id}")

    def list_backtests(self) -> httpx.Response:
        return self.get("/api/v1/user/backtests")

    def save_backtest(self, data: Dict[str, Any]) -> httpx.Response:
        return self.post("/api/v1/user/backtests", json=data)

    def close(self) -> None:
        try:
            self._raw_client.close()
        except Exception:
            pass
