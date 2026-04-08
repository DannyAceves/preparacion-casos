from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Case(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cases"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )
    case_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    case_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text())

    client: Mapped[Client] = relationship("Client", back_populates="cases")
    participants: Mapped[list[Participant]] = relationship(
        "Participant",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    questionnaires: Mapped[list[Questionnaire]] = relationship(
        "Questionnaire",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    questionnaire_answers: Mapped[list[QuestionnaireAnswer]] = relationship(
        "QuestionnaireAnswer",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list[Document]] = relationship(
        "Document",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    document_checklist_items: Mapped[list[CaseDocumentChecklistItem]] = relationship(
        "CaseDocumentChecklistItem",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="CaseDocumentChecklistItem.display_order",
    )
    canonical_fields: Mapped[list[CaseCanonicalField]] = relationship(
        "CaseCanonicalField",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    inconsistencies: Mapped[list[Inconsistency]] = relationship(
        "Inconsistency",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list[Review]] = relationship(
        "Review",
        back_populates="case",
        cascade="all, delete-orphan",
    )
