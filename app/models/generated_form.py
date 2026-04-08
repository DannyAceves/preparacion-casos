from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GeneratedForm(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generated_forms"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
    form_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forms.id"),
        nullable=False,
        index=True,
    )
    draft_version: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    generated_payload: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSONB(), nullable=False)
    warnings_payload: Mapped[list[dict[str, Any]] | dict[str, Any] | None] = mapped_column(JSONB())
    export_path: Mapped[str | None] = mapped_column(String(500))
    review_notes: Mapped[str | None] = mapped_column(Text())
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_by_user_id: Mapped[str | None] = mapped_column(String(255))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    form: Mapped[Form] = relationship("Form", back_populates="generated_forms")
