import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import TimestampedSchema


class ParticipantBase(BaseModel):
    case_id: uuid.UUID
    role: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    date_of_birth: date | None = None
    notes: str | None = None


class ParticipantCreate(ParticipantBase):
    pass


class ParticipantUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: uuid.UUID | None = None
    role: str | None = Field(default=None, min_length=1, max_length=100)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    date_of_birth: date | None = None
    notes: str | None = None


class ParticipantRead(TimestampedSchema, ParticipantBase):
    pass
