from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentClassification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_classifications"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    predicted_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    confidence_score: Mapped[float | None] = mapped_column(Float())
    classification_source: Mapped[str] = mapped_column(String(50), nullable=False, default="automatic", index=True)
    classification_method: Mapped[str] = mapped_column(String(100), nullable=False, default="rules")
    is_override: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True, index=True)
    reviewed_by_user_id: Mapped[str | None] = mapped_column(String(255))
    review_notes: Mapped[str | None] = mapped_column(Text())
    evidence_payload: Mapped[dict | list | None] = mapped_column(JSONB())
