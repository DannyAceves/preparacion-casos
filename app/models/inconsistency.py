from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Inconsistency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inconsistencies"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
    field_key: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="medium", index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open", index=True)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    evidence_payload: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB())
    resolution_notes: Mapped[str | None] = mapped_column(Text())
    resolved_by_user_id: Mapped[str | None] = mapped_column(String(255))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    case: Mapped[Case] = relationship("Case", back_populates="inconsistencies")
