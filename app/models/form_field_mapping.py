from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FormFieldMapping(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "form_field_mappings"

    form_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forms.id"),
        nullable=False,
        index=True,
    )
    form_field_key: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    canonical_field_key: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    section_key: Mapped[str | None] = mapped_column(String(100), index=True)
    section_title: Mapped[str | None] = mapped_column(String(255))
    field_label: Mapped[str | None] = mapped_column(String(255))
    field_type: Mapped[str | None] = mapped_column(String(50), index=True)
    help_text: Mapped[str | None] = mapped_column(Text())
    display_order: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    transform_rule_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB())
    required: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)

    form: Mapped[Form] = relationship("Form", back_populates="field_mappings")
