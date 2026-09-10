"""FastAPI Backend Entrypoint cho hệ thống VN Stock."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import HealthResponse

app = FastAPI(
    title="VN Stock Prediction API",
    description="Backend API phục vụ truy vấn dữ liệu chứng khoán, dự báo AI và kiểm thử chiến lược đầu tư.",
    version="0.1.0",
)

# Cấu hình CORS cho phép Frontend truy cập
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check() -> HealthResponse:
    """Endpoint kiểm tra trạng thái hoạt động của Backend API."""
    return HealthResponse(status="healthy", service="vn-stock-api", version="0.1.0")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
