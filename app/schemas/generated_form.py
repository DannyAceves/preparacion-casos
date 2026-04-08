import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedSchema

GeneratedFormStatus = Literal["draft", "review_pending", "approved", "fix_required"]


class GenerateFormsRequest(BaseModel):
    generated_by_reference: str | None = Field(default=None, max_length=255)
    export_base_path: str | None = Field(default=None, max_length=500)


class GeneratedFormReviewRequest(BaseModel):
    reviewed_by_user_id: str = Field(min_length=1, max_length=255)
    review_notes: str | None = Field(default=None, max_length=2000)


class GeneratedFormTemplateRead(BaseModel):
    form_id: uuid.UUID
    form_code: str
    form_name: str
    version: int
    case_type_id: str


class GeneratedFormSuggestionRead(BaseModel):
    source_type: str
    source_key: str
    source_label: str
    value: Any
    confidence_score: float | None = None
    source_document_id: uuid.UUID | None = None
    source_document_name: str | None = None


class AssistedFormFieldRead(BaseModel):
    form_field_key: str
    canonical_field_key: str
    section_key: str
    section_title: str
    field_label: str
    field_type: str
    help_text: str | None
    required: bool
    display_order: int
    value: Any
    manual_override: bool
    selected_source_key: str | None
    selected_source_label: str | None
    warnings: list[dict[str, Any]]
    suggestions: list[GeneratedFormSuggestionRead]


class AssistedFormSectionRead(BaseModel):
    section_key: str
    section_title: str
    display_order: int
    fields: list[AssistedFormFieldRead]


class AssistedFormWorkspaceRead(BaseModel):
    generated_form_id: uuid.UUID
    case_id: uuid.UUID
    status: GeneratedFormStatus
    form: GeneratedFormTemplateRead
    sections: list[AssistedFormSectionRead]
    warnings: list[dict[str, Any]]


class AssistedFormFieldUpdateRequest(BaseModel):
    actor_reference: str | None = Field(default=None, max_length=255)
    value: Any
    manual_override: bool = True
    selected_source_key: str | None = Field(default=None, max_length=255)
    selected_source_label: str | None = Field(default=None, max_length=255)


class GeneratedFormRead(TimestampedSchema):
    case_id: uuid.UUID
    form_id: uuid.UUID
    draft_version: int
    status: GeneratedFormStatus
    generated_payload: dict[str, Any] | list[Any]
    warnings_payload: list[dict[str, Any]] | dict[str, Any] | None
    export_path: str | None
    review_notes: str | None
    generated_at: datetime
    reviewed_by_user_id: str | None
    reviewed_at: datetime | None


class GeneratedFormDetailRead(GeneratedFormRead):
    form: GeneratedFormTemplateRead
    workspace: AssistedFormWorkspaceRead | None = None
