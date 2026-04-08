import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampedSchema


class CaseBase(BaseModel):
    client_id: uuid.UUID
    case_number: str = Field(min_length=1, max_length=100)
    case_type: str = Field(min_length=1, max_length=100)
    status: str = Field(default="draft", min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=255)
    summary: str | None = None


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: uuid.UUID | None = None
    case_number: str | None = Field(default=None, min_length=1, max_length=100)
    case_type: str | None = Field(default=None, min_length=1, max_length=100)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    summary: str | None = None


class CaseRead(TimestampedSchema, CaseBase):
    pass
