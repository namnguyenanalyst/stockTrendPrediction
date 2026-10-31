"""Pydantic V2 Schemas cho Nhật ký kiểm thử chiến lược (Backtest History)."""

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BacktestHistoryCreateRequest(BaseModel):
    """Payload lưu trữ kết quả kiểm thử chiến lược vào tài khoản."""

    symbol: str = Field(..., min_length=1, description="Mã cổ phiếu")
    strategy_name: str = Field(..., min_length=1, description="Tên chiến lược")
    strategy_type: str = Field(..., min_length=1, description="Loại chiến lược")
    start_date: date = Field(..., description="Ngày bắt đầu kiểm thử")
    end_date: date = Field(..., description="Ngày kết thúc kiểm thử")
    initial_capital: float = Field(..., gt=0, description="Vốn ban đầu (phải > 0)")
    total_return: float = Field(..., description="Tổng tỷ suất sinh lời")
    sharpe_ratio: float = Field(..., description="Chỉ số Sharpe")
    max_drawdown: float = Field(..., description="Mức sụt giảm tối đa")
    win_rate: float = Field(..., description="Tỷ lệ giao dịch thắng")
    equity_curve: list[dict[str, Any]] = Field(
        default_factory=list, description="Chuỗi giá trị tài sản ròng"
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Symbol cannot be empty")
        return cleaned

    @field_validator("equity_curve")
    @classmethod
    def validate_equity_curve(cls, v: Any) -> list[dict[str, Any]]:
        if not isinstance(v, list):
            raise TypeError("equity_curve must be a list")
        return v


class BacktestHistoryResponse(BaseModel):
    """Thông tin nhật ký kiểm thử chiến lược."""

    id: uuid.UUID
    user_id: uuid.UUID
    symbol: str
    strategy_name: str
    strategy_type: str
    start_date: date | str
    end_date: date | str
    initial_capital: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    equity_curve: list[dict[str, Any]]
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)
