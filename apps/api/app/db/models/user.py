"""SQLAlchemy 2.0 Model: User."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.backtest import BacktestHistory
    from app.db.models.preset import StrategyPreset
    from app.db.models.watchlist import UserWatchlist


class UserRole(str, enum.Enum):
    """Phân quyền người dùng trong hệ thống."""

    TRADER = "trader"
    ADMIN = "admin"


class RiskProfile(str, enum.Enum):
    """Khẩu vị rủi ro đầu tư của người dùng."""

    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class User(Base):
    """Bảng người dùng cốt lõi (users) phục vụ xác thực JWT và phân quyền."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.TRADER,
        nullable=False,
    )
    risk_profile: Mapped[RiskProfile] = mapped_column(
        Enum(RiskProfile, name="risk_profile_enum", native_enum=False),
        default=RiskProfile.BALANCED,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships với cascade deletes
    watchlists: Mapped[list["UserWatchlist"]] = relationship(
        "UserWatchlist",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    strategy_presets: Mapped[list["StrategyPreset"]] = relationship(
        "StrategyPreset",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    backtest_histories: Mapped[list["BacktestHistory"]] = relationship(
        "BacktestHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
