import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampedSchema


class DocumentBase(BaseModel):
    case_id: uuid.UUID
    uploaded_by_user_id: str = Field(min_length=1, max_length=255)
    document_type: str = Field(default="unclassified", min_length=1, max_length=100)
    original_filename: str = Field(min_length=1, max_length=255)
    stored_filename: str = Field(min_length=1, max_length=255)
    storage_backend: str = Field(min_length=1, max_length=50)
    storage_key: str = Field(min_length=1, max_length=500)
    mime_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(ge=0)
    sha256_hash: str = Field(min_length=64, max_length=64)
    document_status: str = Field(default="uploaded", min_length=1, max_length=50)
    processing_status: str = Field(default="uploaded", min_length=1, max_length=50)
    classification_label: str | None = Field(default=None, max_length=100)
    classification_source: str | None = Field(default=None, max_length=50)
    classification_confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    file_metadata: dict[str, Any] | None = None
    extracted_text: str | None = None
    extracted_fields: dict[str, Any] | list[Any] | None = None
    extracted_metadata: dict[str, Any] | None = None
    version_number: int = Field(default=1, ge=1)
    is_current: bool = True
    previous_version_id: uuid.UUID | None = None
    root_document_id: uuid.UUID | None = None
    replacement_notes: str | None = None
    uploaded_at: datetime


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: uuid.UUID | None = None
    uploaded_by_user_id: str | None = Field(default=None, min_length=1, max_length=255)
    document_type: str | None = Field(default=None, min_length=1, max_length=100)
    original_filename: str | None = Field(default=None, min_length=1, max_length=255)
    stored_filename: str | None = Field(default=None, min_length=1, max_length=255)
    storage_backend: str | None = Field(default=None, min_length=1, max_length=50)
    storage_key: str | None = Field(default=None, min_length=1, max_length=500)
    mime_type: str | None = Field(default=None, min_length=1, max_length=100)
    size_bytes: int | None = Field(default=None, ge=0)
    sha256_hash: str | None = Field(default=None, min_length=64, max_length=64)
    document_status: str | None = Field(default=None, min_length=1, max_length=50)
    processing_status: str | None = Field(default=None, min_length=1, max_length=50)
    classification_label: str | None = Field(default=None, max_length=100)
    classification_source: str | None = Field(default=None, max_length=50)
    classification_confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    file_metadata: dict[str, Any] | None = None
    extracted_text: str | None = None
    extracted_fields: dict[str, Any] | list[Any] | None = None
    extracted_metadata: dict[str, Any] | None = None
    version_number: int | None = Field(default=None, ge=1)
    is_current: bool | None = None
    previous_version_id: uuid.UUID | None = None
    root_document_id: uuid.UUID | None = None
    replacement_notes: str | None = None
    uploaded_at: datetime | None = None


class DocumentRead(TimestampedSchema, DocumentBase):
    pass


class DocumentClassificationUpdate(BaseModel):
    classification_label: str = Field(min_length=1, max_length=100)
    classification_source: str = Field(min_length=1, max_length=50)
    classification_confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    reviewed_by_user_id: str | None = Field(default=None, min_length=1, max_length=255)
    review_notes: str | None = Field(default=None, max_length=2000)


class DocumentReprocessRequest(BaseModel):
    actor_reference: str = Field(min_length=1, max_length=255)


class DocumentVersionSummaryRead(TimestampedSchema):
    case_id: uuid.UUID
    version_number: int
    is_current: bool
    original_filename: str
    stored_filename: str
    document_status: str
    classification_label: str | None
    uploaded_at: datetime


class DocumentDetailRead(DocumentRead):
    versions: list[DocumentVersionSummaryRead] = Field(default_factory=list)
