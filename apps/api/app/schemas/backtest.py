"""Pydantic V2 Schemas cho Nhật ký kiểm thử chiến lược (Backtest History)."""

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.validation import validate_json_payload


class BacktestHistoryCreateRequest(BaseModel):
    """Payload lưu trữ kết quả kiểm thử chiến lược vào tài khoản."""

    model_config = ConfigDict(allow_inf_nan=False, str_strip_whitespace=True)

    symbol: str = Field(..., min_length=1, max_length=20, description="Mã cổ phiếu")
    strategy_name: str = Field(..., min_length=1, max_length=100, description="Tên chiến lược")
    strategy_type: str = Field(..., min_length=1, max_length=50, description="Loại chiến lược")
    start_date: date = Field(..., description="Ngày bắt đầu kiểm thử")
    end_date: date = Field(..., description="Ngày kết thúc kiểm thử")
    initial_capital: float = Field(..., gt=0, description="Vốn ban đầu (phải > 0)")
    total_return: float = Field(..., description="Tổng tỷ suất sinh lời")
    sharpe_ratio: float | None = Field(..., description="Chỉ số Sharpe")
    max_drawdown: float = Field(..., ge=-100, le=100, description="Mức sụt giảm tối đa (%); nhận dấu âm từ client cũ")
    win_rate: float | None = Field(..., ge=0, le=100, description="Tỷ lệ giao dịch thắng (%)")
    equity_curve: list[dict[str, Any]] = Field(
        default_factory=list, max_length=5000, description="Chuỗi giá trị tài sản ròng"
    )

    config: dict[str, Any] = Field(default_factory=dict, description="Cấu hình và provenance do client gửi, chưa chứng thực")

    @field_validator("config")
    @classmethod
    def validate_config(cls, value):
        return validate_json_payload(value)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must not precede start_date")
        return self

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
        return validate_json_payload(v)


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
    sharpe_ratio: float | None
    max_drawdown: float
    win_rate: float | None
    equity_curve: list[dict[str, Any]]
    config: dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)
