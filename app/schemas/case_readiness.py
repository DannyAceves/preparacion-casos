import uuid
from typing import Literal

from pydantic import BaseModel, Field

CaseTargetStatus = Literal["attorney_review", "ready_for_submission", "submitted"]


class CaseReadinessIssueRead(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "blocking"]


class CaseTargetReadinessRead(BaseModel):
    target_status: CaseTargetStatus
    is_ready: bool
    blockers: list[CaseReadinessIssueRead] = Field(default_factory=list)
    warnings: list[CaseReadinessIssueRead] = Field(default_factory=list)


class CaseReadinessSummaryRead(BaseModel):
    required_document_types: list[str]
    present_required_document_types: list[str]
    missing_required_document_types: list[str]
    open_high_or_critical_inconsistency_count: int
    open_critical_inconsistency_count: int
    unapproved_generated_form_count: int
    generated_form_count: int
    attorney_approved_review_exists: bool


class CaseReadinessRead(BaseModel):
    case_id: uuid.UUID
    case_status: str
    summary: CaseReadinessSummaryRead
    targets: list[CaseTargetReadinessRead]


class CaseReadinessValidateRequest(BaseModel):
    actor_reference: str | None = Field(default=None, max_length=255)


class CaseTransitionRequest(BaseModel):
    target_status: CaseTargetStatus
    actor_reference: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
