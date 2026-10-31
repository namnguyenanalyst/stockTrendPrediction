"""Pydantic V2 Schemas cho Mẫu cấu hình chiến lược (Strategy Preset)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PresetCreateRequest(BaseModel):
    """Payload tạo mới mẫu cấu hình chiến lược."""

    name: str = Field(..., min_length=1, description="Tên mẫu chiến lược")
    description: str | None = Field(default=None, description="Mô tả chiến lược")
    parameters: dict[str, Any] = Field(..., description="Từ điển các tham số định lượng")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Preset name cannot be empty")
        return cleaned

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v: Any) -> dict[str, Any]:
        if not isinstance(v, dict):
            raise TypeError("Parameters must be a JSON dictionary")
        return v


class PresetResponse(BaseModel):
    """Thông tin mẫu cấu hình chiến lược."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None = None
    parameters: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
