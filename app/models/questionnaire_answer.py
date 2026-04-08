from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class QuestionnaireAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "questionnaire_answers"
    __table_args__ = (
        UniqueConstraint("case_id", "question_id", name="uq_questionnaire_answers_case_id_question_id"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaire_questions.id"),
        nullable=False,
        index=True,
    )
    answer_text: Mapped[str | None] = mapped_column(Text())
    answer_date: Mapped[date | None] = mapped_column(Date())
    answer_boolean: Mapped[bool | None] = mapped_column(Boolean())
    answer_choice: Mapped[str | None] = mapped_column(String(255))
    answer_choices: Mapped[list[str] | None] = mapped_column(JSONB())
    answer_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB())

    case: Mapped[Case] = relationship("Case", back_populates="questionnaire_answers")
    question: Mapped[QuestionnaireQuestion] = relationship("QuestionnaireQuestion", back_populates="answers")
