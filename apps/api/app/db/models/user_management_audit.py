"""Persistent account management history; no credentials are stored."""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class UserManagementAudit(Base):
    __tablename__ = "user_management_audits"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    actor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    target_email: Mapped[str] = mapped_column(String(255))
    old_role: Mapped[str] = mapped_column(String(20))
    new_role: Mapped[str] = mapped_column(String(20))
    old_active: Mapped[bool] = mapped_column(Boolean)
    new_active: Mapped[bool] = mapped_column(Boolean)
    source: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
