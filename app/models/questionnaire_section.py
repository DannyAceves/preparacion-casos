from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class QuestionnaireSection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "questionnaire_sections"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaire_templates.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    template: Mapped[QuestionnaireTemplate] = relationship("QuestionnaireTemplate", back_populates="sections")
    questions: Mapped[list[QuestionnaireQuestion]] = relationship(
        "QuestionnaireQuestion",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="QuestionnaireQuestion.display_order",
    )
