"""Pydantic schemas định nghĩa khuôn mẫu dữ liệu cho API."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Trạng thái hệ thống")
    service: str = Field(default="vn-stock-api", description="Tên service")
    version: str = Field(default="0.1.0", description="Phiên bản API")
