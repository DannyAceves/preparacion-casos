from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Consultation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consultations"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    date_of_birth: Mapped[date | None] = mapped_column(Date())
    appointment_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_attorney: Mapped[str | None] = mapped_column(String(255))
    reception_notes: Mapped[str | None] = mapped_column(Text())
    intake_answers: Mapped[str | None] = mapped_column(Text())
    suggested_case_type: Mapped[str | None] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="scheduled", index=True)
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id"),
        nullable=True,
        index=True,
    )
    converted_case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=True,
        unique=True,
        index=True,
    )

    client: Mapped[Client | None] = relationship("Client", back_populates="consultations")
    converted_case: Mapped[Case | None] = relationship("Case", foreign_keys=[converted_case_id])
