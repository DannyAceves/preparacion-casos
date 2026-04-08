from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class QuestionnaireQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "questionnaire_questions"

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaire_sections.id"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(Text(), nullable=False)
    help_text: Mapped[str | None] = mapped_column(Text())
    input_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    options: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB())
    validation_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB())
    conditional_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB())
    field_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB())

    section: Mapped[QuestionnaireSection] = relationship("QuestionnaireSection", back_populates="questions")
    answers: Mapped[list[QuestionnaireAnswer]] = relationship("QuestionnaireAnswer", back_populates="question")
