"""Routers package."""

from app.routers.auth import router as auth_router
from app.routers.backtest import router as backtest_router
from app.routers.prediction import router as prediction_router
from app.routers.stocks import router as stocks_router
from app.routers.user import router as user_router

__all__ = [
    "auth_router",
    "backtest_router",
    "prediction_router",
    "stocks_router",
    "user_router",
]
