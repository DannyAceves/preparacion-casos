import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampedSchema


class DocumentChecklistTemplateItemRead(TimestampedSchema):
    template_id: uuid.UUID
    label: str
    document_type: str | None
    display_order: int
    default_applies: bool
    color_required: bool
    english_translation_required: bool
    signed_copy_required: bool
    original_required: bool
    copy_only: bool
    guidance: str | None


class CaseDocumentChecklistItemBase(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    document_type: str | None = Field(default=None, max_length=100)
    display_order: int = Field(default=0, ge=0)
    applies: bool = True
    requested: bool = False
    received: bool = False
    validated: bool = False
    observations: str | None = None
    color_required: bool = False
    english_translation_required: bool = False
    signed_copy_required: bool = False
    original_required: bool = False
    copy_only: bool = False
    is_manual: bool = False


class CaseDocumentChecklistItemCreate(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    document_type: str | None = Field(default=None, max_length=100)
    observations: str | None = None
    color_required: bool = False
    english_translation_required: bool = False
    signed_copy_required: bool = False
    original_required: bool = False
    copy_only: bool = False


class CaseDocumentChecklistItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, min_length=1, max_length=255)
    document_type: str | None = Field(default=None, max_length=100)
    applies: bool | None = None
    requested: bool | None = None
    received: bool | None = None
    validated: bool | None = None
    observations: str | None = None
    color_required: bool | None = None
    english_translation_required: bool | None = None
    signed_copy_required: bool | None = None
    original_required: bool | None = None
    copy_only: bool | None = None
    display_order: int | None = Field(default=None, ge=0)


class CaseDocumentChecklistItemRead(TimestampedSchema, CaseDocumentChecklistItemBase):
    case_id: uuid.UUID
    template_item_id: uuid.UUID | None
    linked_document_ids: list[uuid.UUID] = Field(default_factory=list)
    linked_document_count: int = 0


class CaseDocumentChecklistProgress(BaseModel):
    total_items: int
    applicable_items: int
    requested_items: int
    received_items: int
    validated_items: int
    percent_complete: int


class CaseDocumentChecklistRead(BaseModel):
    case_id: uuid.UUID
    template_case_type: str | None
    items: list[CaseDocumentChecklistItemRead]
    progress: CaseDocumentChecklistProgress


class CaseDocumentChecklistReorderRequest(BaseModel):
    item_ids: list[uuid.UUID] = Field(min_length=1)
