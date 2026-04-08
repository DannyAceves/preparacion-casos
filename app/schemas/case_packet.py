import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedSchema

PacketStatus = Literal["generated", "stale", "approved"]


class CasePacketGenerateRequest(BaseModel):
    generated_by_reference: str | None = Field(default=None, max_length=255)
    generation_notes: str | None = Field(default=None, max_length=2000)


class PacketDocumentItemRead(BaseModel):
    document_id: uuid.UUID
    document_type: str
    title: str
    original_filename: str
    classification_label: str | None
    classification_confidence_score: float | None
    document_status: str
    processing_status: str
    priority: int
    section: str
    uploaded_at: datetime


class PacketSummaryRead(BaseModel):
    case_id: uuid.UUID
    case_number: str
    case_type: str
    case_status: str
    title: str
    client: dict[str, Any]
    participants: list[dict[str, Any]]
    canonical_fields: list[dict[str, Any]]
    open_inconsistency_count: int
    latest_review: dict[str, Any] | None


class PacketChecklistItemRead(BaseModel):
    item_key: str
    label: str
    status: Literal["ready", "missing", "warning"]
    required: bool = True
    related_document_type: str | None = None
    notes: str | None = None


class PacketExportArtifactRead(BaseModel):
    artifact_type: Literal["case_review_packet"]
    format: Literal["json"]
    generated_at: datetime
    packet_version: int
    sections: list[dict[str, Any]]
    prefilled_forms_placeholder: dict[str, Any]


class CasePacketRead(TimestampedSchema):
    case_id: uuid.UUID
    packet_version: int
    packet_status: PacketStatus
    generated_by_reference: str | None
    summary_payload: PacketSummaryRead | dict[str, Any] | list[Any]
    document_index: list[PacketDocumentItemRead] | dict[str, Any] | list[Any]
    checklist_payload: list[PacketChecklistItemRead] | dict[str, Any] | list[Any]
    export_artifact: PacketExportArtifactRead | dict[str, Any] | list[Any]
    generation_notes: str | None
    generated_at: datetime
