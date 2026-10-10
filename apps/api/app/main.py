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
from app.routers import backtest_router, prediction_router, stocks_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("vn_stock_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời khởi động và tắt ứng dụng FastAPI (Lifespan handler)."""
    logger.info("Khởi động VN Stock API Backend (version %s)...", settings.VERSION)
    logger.info("Đường dẫn dữ liệu: %s", settings.DATA_DIR)
    logger.info("Đường dẫn mô hình: %s", settings.MODELS_DIR)
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
