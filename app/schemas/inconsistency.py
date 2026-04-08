import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampedSchema

InconsistencyStatus = Literal["open", "under_review", "resolved", "dismissed"]
InconsistencySeverity = Literal["low", "medium", "high", "critical"]


class InconsistencyCreateRequest(BaseModel):
    field_key: str = Field(min_length=1, max_length=150)
    severity: InconsistencySeverity
    status: InconsistencyStatus = "open"
    description: str = Field(min_length=1)
    evidence_payload: dict[str, Any] | list[Any] | None = None
    actor_reference: str | None = Field(default=None, max_length=255)


class InconsistencyActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_reference: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class InconsistencyRead(TimestampedSchema):
    case_id: uuid.UUID
    field_key: str
    severity: InconsistencySeverity
    status: InconsistencyStatus
    description: str
    evidence_payload: dict[str, Any] | list[Any] | None
    resolution_notes: str | None
    resolved_by_user_id: str | None
    resolved_at: datetime | None
