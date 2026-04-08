import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.case_questionnaire import (
    CaseQuestionnaireAnswerUpdateRequest,
    CaseQuestionnaireRead,
    QuestionnaireAnswerRead,
)
from app.schemas.document import DocumentRead
from app.schemas.document_checklist import CaseDocumentChecklistRead


class ClientPortalIssueRequest(BaseModel):
    instructions: str | None = None
    expires_in_days: int = Field(default=7, ge=1, le=30)


class ClientPortalAccessRead(BaseModel):
    case_id: uuid.UUID
    token_last4: str
    instructions: str | None
    expires_at: datetime | None
    is_active: bool
    last_accessed_at: datetime | None
    failed_access_attempt_count: int
    last_failed_access_at: datetime | None
    locked_until: datetime | None
    access_session_expires_at: datetime | None


class ClientPortalIssuedRead(ClientPortalAccessRead):
    token: str
    passcode: str
    portal_path: str


class ClientPortalSessionRead(BaseModel):
    session_token: str
    session_expires_at: datetime | None


class ClientPortalAuthRequest(BaseModel):
    token: str = Field(min_length=16)
    passcode: str = Field(min_length=4, max_length=32)


class ClientPortalDocumentUploadResponse(BaseModel):
    document: DocumentRead
    checklist: CaseDocumentChecklistRead


class ClientPortalQuestionAnswerRequest(BaseModel):
    token: str = Field(min_length=16)
    passcode: str = Field(min_length=4, max_length=32)
    payload: CaseQuestionnaireAnswerUpdateRequest


class ClientPortalAnswerCreateRequest(BaseModel):
    token: str = Field(min_length=16)
    passcode: str = Field(min_length=4, max_length=32)
    question_id: uuid.UUID
    value: dict[str, Any]


class ClientPortalProgressRead(BaseModel):
    questionnaire_total_questions: int
    questionnaire_answered_questions: int
    questionnaire_percent_complete: int
    checklist_applicable_items: int
    checklist_received_items: int
    checklist_validated_items: int
    checklist_percent_complete: int
    overall_percent_complete: int


class ClientPortalContextRead(BaseModel):
    case_id: uuid.UUID
    case_number: str
    case_type: str
    case_title: str
    case_summary: str | None
    instructions: str | None
    access_expires_at: datetime | None
    session_token: str
    session_expires_at: datetime | None
    questionnaire: CaseQuestionnaireRead | None
    checklist: CaseDocumentChecklistRead
    documents: list[DocumentRead]
    progress: ClientPortalProgressRead
