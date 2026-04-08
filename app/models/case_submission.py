from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CaseSubmission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "case_submissions"
    __table_args__ = (
        UniqueConstraint("case_id", name="uq_case_submissions_case_id"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    approved_for_submission_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by_user_id: Mapped[str | None] = mapped_column(String(255))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_by_user_id: Mapped[str | None] = mapped_column(String(255))
    submission_reference: Mapped[str | None] = mapped_column(String(255), index=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_by_user_id: Mapped[str | None] = mapped_column(String(255))
    failure_reason: Mapped[str | None] = mapped_column(Text())
