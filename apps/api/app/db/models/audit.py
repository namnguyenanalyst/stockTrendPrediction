"""SQLAlchemy 2.0 Model: PredictionAudit."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base


class PredictionAudit(Base):
    """Bảng kiểm toán dự báo và giám sát độ lệch mô hình (prediction_audits)."""

    __tablename__ = "prediction_audits"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    prediction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    target_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    # 0: Giảm, 1: Đi ngang, 2: Tăng
    predicted_signal: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    # Xác suất phân bổ 3 nhãn: {"down": p0, "neutral": p1, "up": p2}
    predicted_probabilities: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
    )
    actual_return: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    is_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<PredictionAudit(id={self.id}, symbol='{self.symbol}', "
            f"pred_date={self.prediction_date}, signal={self.predicted_signal})>"
        )
