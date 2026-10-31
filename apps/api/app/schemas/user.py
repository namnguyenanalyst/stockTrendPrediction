"""Pydantic V2 Schemas cho người dùng (User)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class UserResponse(BaseModel):
    """Thông tin hồ sơ công khai của người dùng (không chứa hashed_password)."""

    id: uuid.UUID
    email: str
    full_name: str | None = None
    role: str
    risk_profile: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("role", mode="before")
    @classmethod
    def serialize_role(cls, v: object) -> str:
        if hasattr(v, "value"):
            return str(v.value)
        return str(v)

    @field_validator("risk_profile", mode="before")
    @classmethod
    def serialize_risk_profile(cls, v: object) -> str:
        if hasattr(v, "value"):
            return str(v.value)
        return str(v)
