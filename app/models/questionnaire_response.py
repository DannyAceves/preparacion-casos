from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class QuestionnaireResponse(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "questionnaire_responses"

    questionnaire_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaires.id"),
        nullable=False,
        index=True,
    )
    question_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    question_text: Mapped[str] = mapped_column(Text(), nullable=False)
    answer_text: Mapped[str | None] = mapped_column(Text())
    answer_json: Mapped[dict | list | None] = mapped_column(JSONB())

    questionnaire: Mapped[Questionnaire] = relationship("Questionnaire", back_populates="responses")
