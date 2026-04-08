from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class QuestionnaireTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "questionnaire_templates"

    case_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    version: Mapped[int] = mapped_column(nullable=False, default=1)

    sections: Mapped[list[QuestionnaireSection]] = relationship(
        "QuestionnaireSection",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="QuestionnaireSection.display_order",
    )
