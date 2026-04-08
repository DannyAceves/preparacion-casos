from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
    uploaded_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True, default="unclassified")
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(50), nullable=False, default="local")
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    document_status: Mapped[str] = mapped_column(String(50), nullable=False, default="uploaded", index=True)
    processing_status: Mapped[str] = mapped_column(String(50), nullable=False, default="uploaded", index=True)
    classification_label: Mapped[str | None] = mapped_column(String(100), index=True)
    classification_source: Mapped[str | None] = mapped_column(String(50))
    classification_confidence_score: Mapped[float | None] = mapped_column(Float())
    file_metadata: Mapped[dict | None] = mapped_column(JSONB())
    extracted_text: Mapped[str | None] = mapped_column(Text())
    extracted_fields: Mapped[dict | list | None] = mapped_column(JSONB())
    extracted_metadata: Mapped[dict | None] = mapped_column(JSONB())
    version_number: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True, index=True)
    previous_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"))
    root_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"))
    replacement_notes: Mapped[str | None] = mapped_column(Text())
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    case: Mapped[Case] = relationship("Case", back_populates="documents")
    previous_version: Mapped[Document | None] = relationship(
        "Document",
        remote_side="Document.id",
        foreign_keys=[previous_version_id],
    )
    root_document: Mapped[Document | None] = relationship(
        "Document",
        remote_side="Document.id",
        foreign_keys=[root_document_id],
    )
