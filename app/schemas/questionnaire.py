import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampedSchema


class QuestionnaireBase(BaseModel):
    case_id: uuid.UUID
    template_id: uuid.UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    status: str = Field(default="draft", min_length=1, max_length=50)
    version: int = Field(default=1, ge=1)
    template_version: int | None = Field(default=None, ge=1)
    submitted_at: datetime | None = None


class QuestionnaireCreate(QuestionnaireBase):
    pass


class QuestionnaireUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: uuid.UUID | None = None
    template_id: uuid.UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    version: int | None = Field(default=None, ge=1)
    template_version: int | None = Field(default=None, ge=1)
    submitted_at: datetime | None = None


class QuestionnaireRead(TimestampedSchema, QuestionnaireBase):
    pass
