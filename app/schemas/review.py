import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMBaseSchema, TimestampedSchema

ReviewType = Literal["paralegal", "attorney", "qa"]
ReviewDecision = Literal["fix_required", "changes_requested", "approved", "rejected"]


class CaseReviewCreateRequest(BaseModel):
    review_type: ReviewType
    reviewer_reference: str = Field(min_length=1, max_length=255)
    decision: ReviewDecision
    notes: str | None = None
    reviewed_at: datetime | None = None
    actor_reference: str | None = Field(default=None, max_length=255)


class ReviewRead(TimestampedSchema):
    case_id: uuid.UUID
    review_type: ReviewType
    reviewer_reference: str
    decision: ReviewDecision
    notes: str | None
    reviewed_at: datetime | None


class TimelineEventRead(ORMBaseSchema):
    event_type: str
    entity_type: str
    entity_id: str
    action: str
    actor_reference: str | None
    occurred_at: datetime
    payload: dict[str, Any] | list[Any] | None
