from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentChecklistTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_checklist_templates"

    case_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())

    items: Mapped[list[DocumentChecklistTemplateItem]] = relationship(
        "DocumentChecklistTemplateItem",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="DocumentChecklistTemplateItem.display_order",
    )


class DocumentChecklistTemplateItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_checklist_template_items"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_checklist_templates.id"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(100), index=True)
    display_order: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    default_applies: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    color_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    english_translation_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    signed_copy_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    original_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    copy_only: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    guidance: Mapped[str | None] = mapped_column(Text())

    template: Mapped[DocumentChecklistTemplate] = relationship("DocumentChecklistTemplate", back_populates="items")


class CaseDocumentChecklistItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "case_document_checklist_items"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
    template_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_checklist_template_items.id"),
        nullable=True,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(100), index=True)
    display_order: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    applies: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    requested: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    received: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    validated: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    observations: Mapped[str | None] = mapped_column(Text())
    color_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    english_translation_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    signed_copy_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    original_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    copy_only: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    is_manual: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)

    case: Mapped[Case] = relationship("Case", back_populates="document_checklist_items")
    template_item: Mapped[DocumentChecklistTemplateItem | None] = relationship("DocumentChecklistTemplateItem")
