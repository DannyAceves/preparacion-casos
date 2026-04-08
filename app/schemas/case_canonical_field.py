import uuid
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import TimestampedSchema

CanonicalFieldStatus = Literal["suggested", "confirmed", "approved", "rejected"]


class CaseCanonicalFieldBase(BaseModel):
    source_document_id: uuid.UUID | None = None
    field_key: str = Field(min_length=1, max_length=150)
    field_value: dict[str, Any] | list[Any] | str | int | float | bool | None = None
    confidence_score: Decimal | None = Field(default=None, ge=0, le=1)
    source_priority: int = Field(default=0, ge=0)
    status: CanonicalFieldStatus = "suggested"


class CaseCanonicalFieldPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_reference: str | None = Field(default=None, max_length=255)
    source_document_id: uuid.UUID | None = None
    field_value: dict[str, Any] | list[Any] | str | int | float | bool | None = None
    confidence_score: Decimal | None = Field(default=None, ge=0, le=1)
    source_priority: int | None = Field(default=None, ge=0)
    status: CanonicalFieldStatus | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "CaseCanonicalFieldPatchRequest":
        if (
            self.source_document_id is None
            and self.field_value is None
            and self.confidence_score is None
            and self.source_priority is None
            and self.status is None
        ):
            raise ValueError("At least one field must be provided")
        return self


class CaseCanonicalFieldRead(TimestampedSchema, CaseCanonicalFieldBase):
    case_id: uuid.UUID
