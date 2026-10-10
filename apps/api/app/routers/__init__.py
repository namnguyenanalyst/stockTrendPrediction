"""Routers package."""

from app.routers.backtest import router as backtest_router
from app.routers.prediction import router as prediction_router
from app.routers.stocks import router as stocks_router

__all__ = ["backtest_router", "prediction_router", "stocks_router"]
