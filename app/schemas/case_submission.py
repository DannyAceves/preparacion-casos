import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedSchema

CaseSubmissionStatus = Literal["draft", "approved_for_submission", "submitted", "failed"]


class CaseSubmissionApproveRequest(BaseModel):
    approved_by_user_id: str = Field(min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)


class CaseSubmissionSubmitRequest(BaseModel):
    submitted_by_user_id: str = Field(min_length=1, max_length=255)
    submission_reference: str = Field(min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)


class CaseSubmissionFailRequest(BaseModel):
    failed_by_user_id: str = Field(min_length=1, max_length=255)
    failure_reason: str = Field(min_length=1, max_length=2000)


class CaseCloseRequest(BaseModel):
    closed_by_user_id: str = Field(min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)


class CaseSubmissionRead(TimestampedSchema):
    case_id: uuid.UUID
    status: CaseSubmissionStatus
    approved_for_submission_at: datetime | None
    approved_by_user_id: str | None
    submitted_at: datetime | None
    submitted_by_user_id: str | None
    submission_reference: str | None
    failed_at: datetime | None
    failed_by_user_id: str | None
    failure_reason: str | None
