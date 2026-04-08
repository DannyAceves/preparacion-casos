from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedSchema


class DocumentClassificationCreate(BaseModel):
    case_id: uuid.UUID
    document_id: uuid.UUID
    version_number: int = Field(ge=1)
    predicted_type: str = Field(min_length=1, max_length=100)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    classification_source: str = Field(min_length=1, max_length=50)
    classification_method: str = Field(min_length=1, max_length=100)
    is_override: bool = False
    is_active: bool = True
    reviewed_by_user_id: str | None = Field(default=None, min_length=1, max_length=255)
    review_notes: str | None = Field(default=None, max_length=2000)
    evidence_payload: dict[str, Any] | list[Any] | None = None


class DocumentClassificationRead(TimestampedSchema):
    case_id: uuid.UUID
    document_id: uuid.UUID
    version_number: int
    predicted_type: str
    confidence_score: float | None
    classification_source: str
    classification_method: str
    is_override: bool
    is_active: bool
    reviewed_by_user_id: str | None
    review_notes: str | None
    evidence_payload: dict[str, Any] | list[Any] | None
