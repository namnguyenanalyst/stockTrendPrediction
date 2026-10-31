"""SQLAlchemy 2.0 Declarative Base cho toàn bộ ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class kế thừa cho toàn bộ models trong hệ thống VN Stock."""
