import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AllowedInputType = Literal[
    "text",
    "textarea",
    "date",
    "checkbox",
    "radio",
    "select",
    "repeatable_group",
    "boolean",
    "single_select",
    "multi_select",
    "json",
]


class QuestionnaireAnswerPayload(BaseModel):
    answer_text: str | None = None
    answer_date: date | None = None
    answer_boolean: bool | None = None
    answer_choice: str | None = None
    answer_choices: list[str] | None = None
    answer_json: dict[str, Any] | list[Any] | None = None

    @model_validator(mode="after")
    def validate_at_least_one_value(self) -> "QuestionnaireAnswerPayload":
        if not any(
            value is not None
            for value in (
                self.answer_text,
                self.answer_date,
                self.answer_boolean,
                self.answer_choice,
                self.answer_choices,
                self.answer_json,
            )
        ):
            raise ValueError("At least one answer value must be provided")
        return self


class CaseQuestionnaireAnswerUpsert(BaseModel):
    question_id: uuid.UUID
    value: QuestionnaireAnswerPayload


class CaseQuestionnaireAnswersUpsertRequest(BaseModel):
    actor_reference: str | None = Field(default=None, max_length=255)
    answers: list[CaseQuestionnaireAnswerUpsert] = Field(min_length=1)


class CaseQuestionnaireAnswerUpdateRequest(BaseModel):
    actor_reference: str | None = Field(default=None, max_length=255)
    value: QuestionnaireAnswerPayload


class QuestionnaireAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    question_id: uuid.UUID
    answer_text: str | None
    answer_date: date | None
    answer_boolean: bool | None
    answer_choice: str | None
    answer_choices: list[str] | None
    answer_json: dict[str, Any] | list[Any] | None
    created_at: datetime
    updated_at: datetime


class QuestionnaireQuestionOptionRead(BaseModel):
    label: str
    value: str


class QuestionnaireQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    prompt: str
    help_text: str | None
    input_type: AllowedInputType
    is_required: bool
    display_order: int
    options: list[QuestionnaireQuestionOptionRead] | None
    validation_rules: dict[str, Any] | None
    conditional_rules: dict[str, Any] | None
    field_config: dict[str, Any] | None
    answer: QuestionnaireAnswerRead | None = None


class QuestionnaireSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    display_order: int
    questions: list[QuestionnaireQuestionRead]


class QuestionnaireTemplateSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_type: str
    title: str
    description: str | None
    status: str
    version: int


class CaseQuestionnaireRead(BaseModel):
    case_id: uuid.UUID
    case_type: str
    questionnaire: QuestionnaireTemplateSummaryRead
    questionnaire_instance_id: uuid.UUID | None = None
    questionnaire_instance_status: str | None = None
    questionnaire_instance_version: int | None = None
    sections: list[QuestionnaireSectionRead]
