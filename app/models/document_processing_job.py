from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentProcessingJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_processing_jobs"
    __table_args__ = (
        UniqueConstraint("document_id", "job_type", "version_number", name="uq_document_processing_jobs_doc_job_version"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer(), nullable=False, default=3)
    version_number: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    payload: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB())
    error_message: Mapped[str | None] = mapped_column(Text())
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
