"""FastAPI Backend Entrypoint cho hệ thống VN Stock.

Tích hợp toàn diện:
- Router dữ liệu cổ phiếu & chỉ báo kỹ thuật: /api/stocks
- Router suy luận dự báo AI: /api/predict
- Router mô phỏng kiểm thử chiến lược đầu tư: /api/backtest
- Endpoint kiểm tra sức khỏe hệ thống: /health
"""

import logging
import os
from contextlib import asynccontextmanager

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.models.schemas import HealthResponse
from app.routers import (
    auth_router,
    backtest_router,
    prediction_router,
    stocks_router,
    user_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("vn_stock_api")


async def run_startup_sync():
    """Tự động kiểm tra và đồng bộ nến thị trường mới nhất trong nền khi khởi động."""
    import asyncio
    await asyncio.sleep(0.5)  # Nhường event loop cho server mở port ngay lập tức
    try:
        from vn_stock.market_session import get_target_market_session_info
        session = get_target_market_session_info()
        logger.info(
            "Kiểm tra phiên thị trường khởi động: Mục tiêu nến %s (%s)",
            session["target_date"],
            session["session_name"],
        )
        from vn_stock.data_ingestion import sync_latest_market_data
        res = sync_latest_market_data(force=False)
        logger.info("Hoàn tất kiểm tra đồng bộ nến thị trường: %s", res.get("status"))
    except Exception as exc:
        logger.warning("Không thể tự động đồng bộ khi khởi động (sử dụng cache hiện có): %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời khởi động và tắt ứng dụng FastAPI (Lifespan handler)."""
    import asyncio

    logger.info("Khởi động VN Stock API Backend (version %s)...", settings.VERSION)
    logger.info("Đường dẫn dữ liệu: %s", settings.DATA_DIR)
    logger.info("Đường dẫn mô hình: %s", settings.MODELS_DIR)

    if settings.AUTO_SYNC_ON_STARTUP:
        asyncio.create_task(run_startup_sync())

    yield
    logger.info("Đang tắt dịch vụ VN Stock API Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Cấu hình CORS cho phép kết nối từ Frontend Next.js Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các Router nghiệp vụ dưới prefix /api
app.include_router(stocks_router, prefix=settings.API_V1_STR)
app.include_router(prediction_router, prefix=settings.API_V1_STR)
app.include_router(backtest_router, prefix=settings.API_V1_STR)

# Đăng ký các Router xác thực và cá nhân hóa dưới prefix /api/v1
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(user_router, prefix="/api/v1/user", tags=["User"])


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Monitoring"],
    summary="Kiểm tra trạng thái hoạt động của Backend API",
)
async def health_check() -> HealthResponse:
    """Endpoint kiểm tra trạng thái hoạt động (Healthcheck endpoint)."""
    return HealthResponse(
        status="healthy",
        service="vn-stock-api",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
