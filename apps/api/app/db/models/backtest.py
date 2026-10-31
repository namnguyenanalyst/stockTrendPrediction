"""SQLAlchemy 2.0 Model: BacktestHistory."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class BacktestHistory(Base):
    """Lịch sử thực thi kiểm thử chiến lược định lượng (backtest_histories)."""

    __tablename__ = "backtest_histories"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    strategy_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    strategy_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    initial_capital: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    total_return: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    sharpe_ratio: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    max_drawdown: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    win_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    # Chuỗi dữ liệu Equity Curve theo thời gian phục vụ vẽ biểu đồ
    equity_curve: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="backtest_histories",
    )

    def __repr__(self) -> str:
        return (
            f"<BacktestHistory(id={self.id}, user_id={self.user_id}, "
            f"symbol='{self.symbol}', total_return={self.total_return:.2%})>"
        )
