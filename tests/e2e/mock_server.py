"""In-process Contract Reference Server for Opaque-Box E2E Testing.

Implements 100% of the REST API specifications defined in:
- PROJECT.md § Interface Contracts
- ORIGINAL_REQUEST.md R1, R2

Enables full Progressive Testability across all tiers without external server dependencies.
"""

import base64
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

SECRET_KEY = "test-secret-key-for-e2e-contracts-jwt-validation-32chars"
ALGORITHM = "HS256"


# -----------------------------------------------------------------------------
# Lightweight Portable JWT & Hashing Engine
# -----------------------------------------------------------------------------

def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _base64url_decode(s: str) -> bytes:
    padding = 4 - (len(s) % 4)
    if padding and padding < 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s.encode("utf-8"))


def create_jwt_token(payload: dict, expires_in_seconds: int = 1800) -> str:
    header = {"typ": "JWT", "alg": ALGORITHM}
    now = int(time.time())
    full_payload = dict(payload)
    full_payload["iat"] = now
    full_payload["exp"] = now + expires_in_seconds

    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(full_payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _base64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_jwt_token(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    actual_sig = _base64url_decode(sig_b64)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid JWT signature")
    payload = json.loads(_base64url_decode(payload_b64).decode("utf-8"))
    if "exp" in payload and payload["exp"] < time.time():
        raise ValueError("JWT has expired")
    return payload


def hash_password(password: str) -> str:
    salt = "fixed_salt_for_testing"
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
# In-Memory State Store
# -----------------------------------------------------------------------------

class InMemoryStore:
    def __init__(self):
        self.users: Dict[str, dict] = {}          # user_id -> user_dict
        self.users_by_email: Dict[str, str] = {}  # email.lower() -> user_id
        self.watchlists: Dict[str, dict] = {}      # watchlist_id -> watchlist_dict
        self.presets: Dict[str, dict] = {}         # preset_id -> preset_dict
        self.backtests: Dict[str, dict] = {}       # backtest_id -> backtest_dict

    def clear(self):
        self.users.clear()
        self.users_by_email.clear()
        self.watchlists.clear()
        self.presets.clear()
        self.backtests.clear()


STORE = InMemoryStore()


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------

class UserRegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    risk_profile: Optional[str] = "balanced"


class UserLoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


class WatchlistCreateRequest(BaseModel):
    name: str
    symbols: List[str]


class PresetCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any]


class BacktestHistoryCreateRequest(BaseModel):
    symbol: str
    strategy_name: str
    strategy_type: str
    start_date: str
    end_date: str
    initial_capital: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    equity_curve: List[Dict[str, Any]]


class BacktestRunRequest(BaseModel):
    symbol: str
    strategy_type: str = "macd_crossover"
    start_date: str = "2023-01-01"
    end_date: str = "2023-12-31"
    initial_capital: float = 100_000_000.0
    parameters: Optional[Dict[str, Any]] = None


# -----------------------------------------------------------------------------
# Dependency: Current User Authentication
# -----------------------------------------------------------------------------

async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Not authenticated")
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    token = parts[1]
    try:
        payload = decode_jwt_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(exc)}")

    user_id = payload.get("sub")
    if not user_id or user_id not in STORE.users:
        raise HTTPException(status_code=401, detail="User not found")
    user = STORE.users[user_id]
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


# -----------------------------------------------------------------------------
# Application Factory
# -----------------------------------------------------------------------------

def create_reference_app() -> FastAPI:
    app = FastAPI(
        title="VN Stock Reference Platform",
        version="0.1.0",
        description="Reference Contract Engine for Opaque-Box E2E Testing",
    )

    # -------------------------------------------------------------------------
    # Backward-Compatible Stock & Quant Endpoints
    # -------------------------------------------------------------------------

    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "service": "vn-stock-api",
            "version": "0.1.0",
            "environment": "test",
        }

    @app.get("/api/stocks/symbols")
    async def stock_symbols():
        return [
            {"symbol": "VIC", "name": "Vingroup", "exchange": "HOSE"},
            {"symbol": "HPG", "name": "Hoa Phat Group", "exchange": "HOSE"},
            {"symbol": "FPT", "name": "FPT Corp", "exchange": "HOSE"},
            {"symbol": "VNM", "name": "Vinamilk", "exchange": "HOSE"},
            {"symbol": "MWG", "name": "Mobile World", "exchange": "HOSE"},
            {"symbol": "TCB", "name": "Techcombank", "exchange": "HOSE"},
        ]

    @app.get("/api/stocks/history")
    async def stock_history(symbol: str, limit: int = 10):
        if limit <= 0:
            raise HTTPException(status_code=422, detail="Limit must be positive")
        bars = [
            {
                "date": f"2024-01-{i+1:02d}",
                "open": 50000.0 + i * 100,
                "high": 51000.0 + i * 100,
                "low": 49500.0 + i * 100,
                "close": 50500.0 + i * 100,
                "volume": 1_000_000 + i * 50_000,
            }
            for i in range(limit)
        ]
        return {"symbol": symbol, "bars": bars, "count": len(bars)}

    @app.get("/api/stocks/indicators")
    async def stock_indicators(symbol: str, limit: int = 5):
        indicators = [
            {
                "date": f"2024-01-{i+1:02d}",
                "close": 50000.0 + i * 100,
                "open_close_ratio": 1.01,
                "sma_20_dev": 0.02,
                "rsi_14": 55.4,
                "cv_50": 0.015,
            }
            for i in range(limit)
        ]
        return {"symbol": symbol, "indicators": indicators, "count": len(indicators)}

    @app.post("/api/predict/direction")
    async def predict_direction(payload: Dict[str, Any]):
        symbol = payload.get("symbol")
        if not symbol:
            raise HTTPException(status_code=422, detail="Symbol required")
        if symbol not in ["VIC", "HPG", "FPT", "VNM", "MWG", "TCB"]:
            raise HTTPException(status_code=404, detail="Symbol not found in coverage universe")
        return {
            "symbol": symbol,
            "target_horizon": "T+3",
            "predicted_signal": 2,
            "direction_label": "Tăng (Bullish)",
            "predicted_probabilities": {
                "down": 0.15,
                "neutral": 0.25,
                "up": 0.60,
            },
            "as_of_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }

    @app.post("/api/backtest/run")
    async def run_backtest(req: BacktestRunRequest):
        if req.initial_capital <= 0:
            raise HTTPException(status_code=422, detail="initial_capital must be greater than 0")
        if req.start_date > req.end_date:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")

        # Standard simulated backtest incorporating Vietnam microstructure fees (0.15% fee, 0.10% tax)
        # and generating valid equity curve points
        curve = [
            {"date": req.start_date, "equity": req.initial_capital, "cash": req.initial_capital, "holdings": 0},
            {"date": "2023-06-15", "equity": req.initial_capital * 1.08, "cash": req.initial_capital * 0.2, "holdings": req.initial_capital * 0.88},
            {"date": req.end_date, "equity": req.initial_capital * 1.155, "cash": req.initial_capital * 1.155, "holdings": 0},
        ]
        return {
            "symbol": req.symbol,
            "strategy_type": req.strategy_type,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "initial_capital": req.initial_capital,
            "final_equity": req.initial_capital * 1.155,
            "total_return": 0.155,
            "sharpe_ratio": 1.42,
            "sortino_ratio": 1.85,
            "max_drawdown": -0.062,
            "win_rate": 0.65,
            "total_trades": 12,
            "fee_rate": 0.0015,
            "tax_rate": 0.0010,
            "settlement_cycle": "T+2.5",
            "equity_curve": curve,
        }

    # -------------------------------------------------------------------------
    # Authentication Router: /api/v1/auth
    # -------------------------------------------------------------------------

    @app.post("/api/v1/auth/register", status_code=201)
    async def auth_register(req: UserRegisterRequest):
        email_clean = req.email.strip().lower()
        if "@" not in email_clean or "." not in email_clean:
            raise HTTPException(status_code=422, detail="Invalid email format")
        if len(req.password) < 8:
            raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
        if req.risk_profile not in ["conservative", "balanced", "aggressive"]:
            raise HTTPException(status_code=422, detail="Invalid risk profile")

        if email_clean in STORE.users_by_email:
            raise HTTPException(status_code=400, detail="Email already registered")

        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        user_record = {
            "id": user_id,
            "email": email_clean,
            "hashed_password": hash_password(req.password),
            "full_name": req.full_name,
            "role": "trader",
            "risk_profile": req.risk_profile or "balanced",
            "is_active": True,
            "created_at": created_at,
            "updated_at": created_at,
        }
        STORE.users[user_id] = user_record
        STORE.users_by_email[email_clean] = user_id

        # Return public profile (excluding password)
        return {
            "id": user_record["id"],
            "email": user_record["email"],
            "full_name": user_record["full_name"],
            "role": user_record["role"],
            "risk_profile": user_record["risk_profile"],
            "is_active": user_record["is_active"],
            "created_at": user_record["created_at"],
        }

    @app.post("/api/v1/auth/login")
    async def auth_login(req: UserLoginRequest, response: Response):
        email_clean = req.email.strip().lower()
        user_id = STORE.users_by_email.get(email_clean)
        if not user_id:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        user = STORE.users[user_id]
        if user["hashed_password"] != hash_password(req.password):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        if not user.get("is_active", True):
            raise HTTPException(status_code=400, detail="Inactive user account")

        access_token = create_jwt_token({"sub": user_id, "email": email_clean, "role": user["role"]}, expires_in_seconds=1800)
        refresh_token = create_jwt_token({"sub": user_id, "type": "refresh"}, expires_in_seconds=86400 * 7)

        # Set HTTP-only Cookie for refresh token
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            path="/api/v1/auth",
            samesite="lax",
            max_age=86400 * 7,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "risk_profile": user["risk_profile"],
                "is_active": user["is_active"],
            },
        }

    @app.post("/api/v1/auth/refresh")
    async def auth_refresh(request: Request, req: RefreshRequest):
        # Read from cookie first, then body
        token = request.cookies.get("refresh_token") or req.refresh_token
        if not token:
            raise HTTPException(status_code=401, detail="Missing refresh token")
        try:
            payload = decode_jwt_token(token)
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
            user_id = payload.get("sub")
            if not user_id or user_id not in STORE.users:
                raise HTTPException(status_code=401, detail="User not found")
            user = STORE.users[user_id]
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        new_access_token = create_jwt_token({"sub": user_id, "email": user["email"], "role": user["role"]}, expires_in_seconds=1800)
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

    @app.get("/api/v1/auth/me")
    async def auth_me(current_user: dict = Depends(get_current_user)):
        return {
            "id": current_user["id"],
            "email": current_user["email"],
            "full_name": current_user["full_name"],
            "role": current_user["role"],
            "risk_profile": current_user["risk_profile"],
            "is_active": current_user["is_active"],
        }

    # -------------------------------------------------------------------------
    # Personalization Router: /api/v1/user
    # -------------------------------------------------------------------------

    @app.get("/api/v1/user/watchlists")
    async def list_watchlists(current_user: dict = Depends(get_current_user)):
        user_id = current_user["id"]
        results = [w for w in STORE.watchlists.values() if w["user_id"] == user_id]
        return results

    @app.post("/api/v1/user/watchlists", status_code=201)
    async def create_watchlist(
        req: WatchlistCreateRequest,
        current_user: dict = Depends(get_current_user),
    ):
        if not req.name or not req.name.strip():
            raise HTTPException(status_code=422, detail="Watchlist name cannot be empty")
        if not isinstance(req.symbols, list) or len(req.symbols) == 0:
            raise HTTPException(status_code=422, detail="Symbols must be a non-empty list of ticker strings")
        for sym in req.symbols:
            if not isinstance(sym, str) or not sym.strip():
                raise HTTPException(status_code=422, detail="Invalid symbol in list")

        wid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "id": wid,
            "user_id": current_user["id"],
            "name": req.name.strip(),
            "symbols": [s.strip().upper() for s in req.symbols],
            "created_at": now,
            "updated_at": now,
        }
        STORE.watchlists[wid] = item
        return item

    @app.delete("/api/v1/user/watchlists/{watchlist_id}", status_code=204)
    async def delete_watchlist(
        watchlist_id: str,
        current_user: dict = Depends(get_current_user),
    ):
        item = STORE.watchlists.get(watchlist_id)
        # IDOR prevention: return 404 if item belongs to another tenant or does not exist
        if not item or item["user_id"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        del STORE.watchlists[watchlist_id]
        return Response(status_code=204)

    @app.get("/api/v1/user/presets")
    async def list_presets(current_user: dict = Depends(get_current_user)):
        user_id = current_user["id"]
        return [p for p in STORE.presets.values() if p["user_id"] == user_id]

    @app.post("/api/v1/user/presets", status_code=201)
    async def create_preset(
        req: PresetCreateRequest,
        current_user: dict = Depends(get_current_user),
    ):
        if not req.name or not req.name.strip():
            raise HTTPException(status_code=422, detail="Preset name cannot be empty")
        if not isinstance(req.parameters, dict):
            raise HTTPException(status_code=422, detail="Parameters must be a JSON dictionary")

        pid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "id": pid,
            "user_id": current_user["id"],
            "name": req.name.strip(),
            "description": req.description,
            "parameters": req.parameters,
            "created_at": now,
            "updated_at": now,
        }
        STORE.presets[pid] = item
        return item

    @app.delete("/api/v1/user/presets/{preset_id}", status_code=204)
    async def delete_preset(
        preset_id: str,
        current_user: dict = Depends(get_current_user),
    ):
        item = STORE.presets.get(preset_id)
        if not item or item["user_id"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Strategy preset not found")
        del STORE.presets[preset_id]
        return Response(status_code=204)

    @app.get("/api/v1/user/backtests")
    async def list_backtests(current_user: dict = Depends(get_current_user)):
        user_id = current_user["id"]
        items = [b for b in STORE.backtests.values() if b["user_id"] == user_id]
        # Return sorted by executed_at descending
        items.sort(key=lambda x: x["executed_at"], reverse=True)
        return items

    @app.post("/api/v1/user/backtests", status_code=201)
    async def save_backtest(
        req: BacktestHistoryCreateRequest,
        current_user: dict = Depends(get_current_user),
    ):
        if req.initial_capital <= 0:
            raise HTTPException(status_code=422, detail="initial_capital must be greater than 0")
        if not isinstance(req.equity_curve, list):
            raise HTTPException(status_code=422, detail="equity_curve must be a list")

        bid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "id": bid,
            "user_id": current_user["id"],
            "symbol": req.symbol.strip().upper(),
            "strategy_name": req.strategy_name,
            "strategy_type": req.strategy_type,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "initial_capital": req.initial_capital,
            "total_return": req.total_return,
            "sharpe_ratio": req.sharpe_ratio,
            "max_drawdown": req.max_drawdown,
            "win_rate": req.win_rate,
            "equity_curve": req.equity_curve,
            "executed_at": now,
        }
        STORE.backtests[bid] = item
        return item

    return app
