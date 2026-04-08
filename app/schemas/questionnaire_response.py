import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampedSchema


class QuestionnaireResponseBase(BaseModel):
    questionnaire_id: uuid.UUID
    question_key: str = Field(min_length=1, max_length=100)
    question_text: str = Field(min_length=1)
    answer_text: str | None = None
    answer_json: dict[str, Any] | list[Any] | None = None


class QuestionnaireResponseCreate(QuestionnaireResponseBase):
    pass


class QuestionnaireResponseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questionnaire_id: uuid.UUID | None = None
    question_key: str | None = Field(default=None, min_length=1, max_length=100)
    question_text: str | None = Field(default=None, min_length=1)
    answer_text: str | None = None
    answer_json: dict[str, Any] | list[Any] | None = None


class QuestionnaireResponseRead(TimestampedSchema, QuestionnaireResponseBase):
    pass
