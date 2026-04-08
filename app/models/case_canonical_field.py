from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CaseCanonicalField(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "case_canonical_fields"
    __table_args__ = (
        UniqueConstraint("case_id", "field_key", name="uq_case_canonical_fields_case_id_field_key"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
    )
    field_key: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    field_value: Mapped[dict[str, Any] | list[Any] | str | int | float | bool | None] = mapped_column(JSONB())
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    source_priority: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="suggested", index=True)

    case: Mapped[Case] = relationship("Case", back_populates="canonical_fields")
    source_document: Mapped[Document | None] = relationship("Document")
