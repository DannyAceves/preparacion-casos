from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ClientPortalAccess(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "client_portal_accesses"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    token_last4: Mapped[str] = mapped_column(String(4), nullable=False)
    passcode_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    access_session_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    access_session_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    instructions: Mapped[str | None] = mapped_column(Text())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True, index=True)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_access_attempt_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    last_failed_access_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    case: Mapped[Case] = relationship("Case")
