from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auth import SystemRole
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SystemUser(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "system_users"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    role: Mapped[SystemRole] = mapped_column(
        Enum(SystemRole, name="system_role_enum", values_callable=lambda values: [value.value for value in values]),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
