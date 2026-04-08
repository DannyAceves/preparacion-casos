from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Form(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "forms"

    case_type_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    form_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    form_name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True, index=True)

    field_mappings: Mapped[list[FormFieldMapping]] = relationship(
        "FormFieldMapping",
        back_populates="form",
        cascade="all, delete-orphan",
    )
    generated_forms: Mapped[list[GeneratedForm]] = relationship(
        "GeneratedForm",
        back_populates="form",
        cascade="all, delete-orphan",
    )
