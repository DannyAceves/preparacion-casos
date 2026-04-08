import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.case import CaseRead
from app.schemas.client import ClientRead
from app.schemas.common import TimestampedSchema


class ConsultationBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    date_of_birth: date | None = None
    appointment_at: datetime | None = None
    assigned_attorney: str | None = Field(default=None, max_length=255)
    reception_notes: str | None = None
    intake_answers: str | None = None
    suggested_case_type: str | None = Field(default=None, max_length=100)
    status: str = Field(default="scheduled", min_length=1, max_length=50)


class ConsultationCreate(ConsultationBase):
    pass


class ConsultationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    date_of_birth: date | None = None
    appointment_at: datetime | None = None
    assigned_attorney: str | None = Field(default=None, max_length=255)
    reception_notes: str | None = None
    intake_answers: str | None = None
    suggested_case_type: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, min_length=1, max_length=50)


class ConsultationRead(TimestampedSchema, ConsultationBase):
    client_id: uuid.UUID | None
    converted_case_id: uuid.UUID | None


class ConsultationConvertToCaseRequest(BaseModel):
    case_number: str = Field(min_length=1, max_length=100)
    case_type: str | None = Field(default=None, min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    summary: str | None = None


class ConsultationConversionResult(BaseModel):
    consultation: ConsultationRead
    client: ClientRead
    case: CaseRead
