import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import TimestampedSchema


TemplateInputType = Literal[
    "text",
    "textarea",
    "date",
    "checkbox",
    "radio",
    "select",
    "repeatable_group",
]


class QuestionnaireTemplateQuestionOption(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1, max_length=255)


class QuestionnaireTemplateQuestionBase(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=1)
    help_text: str | None = None
    input_type: TemplateInputType
    is_required: bool = False
    display_order: int = Field(default=0, ge=0)
    options: list[QuestionnaireTemplateQuestionOption] | None = None
    validation_rules: dict[str, Any] | None = None
    conditional_rules: dict[str, Any] | None = None
    field_config: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_options_for_input_type(self) -> "QuestionnaireTemplateQuestionBase":
        if self.input_type in {"radio", "select"} and not self.options:
            raise ValueError("radio and select questions require options")
        if self.input_type not in {"radio", "select"} and self.options:
            return self
        return self


class QuestionnaireTemplateQuestionCreate(QuestionnaireTemplateQuestionBase):
    pass


class QuestionnaireTemplateQuestionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str | None = Field(default=None, min_length=1, max_length=100)
    prompt: str | None = Field(default=None, min_length=1)
    help_text: str | None = None
    input_type: TemplateInputType | None = None
    is_required: bool | None = None
    display_order: int | None = Field(default=None, ge=0)
    options: list[QuestionnaireTemplateQuestionOption] | None = None
    validation_rules: dict[str, Any] | None = None
    conditional_rules: dict[str, Any] | None = None
    field_config: dict[str, Any] | None = None


class QuestionnaireTemplateQuestionRead(TimestampedSchema, QuestionnaireTemplateQuestionBase):
    section_id: uuid.UUID


class QuestionnaireTemplateSectionBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    display_order: int = Field(default=0, ge=0)


class QuestionnaireTemplateSectionCreate(QuestionnaireTemplateSectionBase):
    questions: list[QuestionnaireTemplateQuestionCreate] = Field(default_factory=list)


class QuestionnaireTemplateSectionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    display_order: int | None = Field(default=None, ge=0)
    questions: list[QuestionnaireTemplateQuestionCreate] | None = None


class QuestionnaireTemplateSectionRead(TimestampedSchema, QuestionnaireTemplateSectionBase):
    template_id: uuid.UUID
    questions: list[QuestionnaireTemplateQuestionRead]


class QuestionnaireTemplateBuilderCreate(BaseModel):
    case_type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: Literal["draft", "active", "archived"] = "draft"
    sections: list[QuestionnaireTemplateSectionCreate] = Field(default_factory=list)


class QuestionnaireTemplateBuilderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: Literal["draft", "active", "archived"] | None = None
    sections: list[QuestionnaireTemplateSectionCreate] | None = None


class QuestionnaireTemplateVersionCreate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: Literal["draft", "active", "archived"] = "draft"


class QuestionnaireTemplateBuilderRead(TimestampedSchema):
    case_type: str
    title: str
    description: str | None
    status: str
    version: int
    sections: list[QuestionnaireTemplateSectionRead]


class QuestionnaireInstanceCreate(BaseModel):
    template_id: uuid.UUID | None = None


class QuestionnaireInstanceRead(TimestampedSchema):
    id: uuid.UUID
    case_id: uuid.UUID
    template_id: uuid.UUID | None
    title: str
    status: str
    version: int
    template_version: int | None
