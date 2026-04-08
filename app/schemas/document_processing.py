import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedSchema

DocumentJobType = Literal[
    "virus_scan_document",
    "ocr_document",
    "classify_document",
    "extract_document_fields",
    "refresh_canonical_fields",
    "detect_case_inconsistencies",
]
DocumentJobStatus = Literal["queued", "running", "completed", "failed", "retrying"]


class DocumentProcessingJobCreate(BaseModel):
    case_id: uuid.UUID
    document_id: uuid.UUID
    job_type: DocumentJobType
    status: DocumentJobStatus = "queued"
    attempts: int = 0
    max_attempts: int = Field(default=3, ge=1)
    version_number: int = Field(default=1, ge=1)
    payload: dict[str, Any] | list[Any] | None = None
    error_message: str | None = None
    queued_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class DocumentProcessingJobRead(TimestampedSchema):
    case_id: uuid.UUID
    document_id: uuid.UUID
    job_type: DocumentJobType
    status: DocumentJobStatus
    attempts: int
    max_attempts: int
    version_number: int
    payload: dict[str, Any] | list[Any] | None
    error_message: str | None
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class QueueJobMessage(BaseModel):
    job_id: uuid.UUID
    case_id: uuid.UUID
    document_id: uuid.UUID
    job_type: DocumentJobType
    version_number: int
    trigger: str
