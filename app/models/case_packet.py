from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CasePacket(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "case_packets"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
    packet_version: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    packet_status: Mapped[str] = mapped_column(String(50), nullable=False, default="generated", index=True)
    generated_by_reference: Mapped[str | None] = mapped_column(String(255))
    summary_payload: Mapped[dict | list] = mapped_column(JSONB(), nullable=False)
    document_index: Mapped[dict | list] = mapped_column(JSONB(), nullable=False)
    checklist_payload: Mapped[dict | list] = mapped_column(JSONB(), nullable=False)
    export_artifact: Mapped[dict | list] = mapped_column(JSONB(), nullable=False)
    generation_notes: Mapped[str | None] = mapped_column(Text())
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
