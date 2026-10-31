"""Pydantic V2 Schemas cho Danh mục theo dõi (Watchlist)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WatchlistCreateRequest(BaseModel):
    """Payload tạo mới danh mục theo dõi."""

    name: str = Field(..., min_length=1, description="Tên danh mục theo dõi")
    symbols: list[str] = Field(..., min_length=1, description="Danh sách mã cổ phiếu")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Watchlist name cannot be empty")
        return cleaned

    @field_validator("symbols")
    @classmethod
    def validate_symbols(cls, v: list[str]) -> list[str]:
        if not isinstance(v, list) or len(v) == 0:
            raise ValueError("Symbols must be a non-empty list of ticker strings")
        cleaned_symbols: list[str] = []
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("Invalid symbol in list")
            cleaned_symbols.append(item.strip().upper())
        return cleaned_symbols


class WatchlistResponse(BaseModel):
    """Thông tin danh mục theo dõi."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    symbols: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
