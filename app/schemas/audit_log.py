import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMBaseSchema


class AuditLogBase(BaseModel):
    case_id: uuid.UUID | None = None
    entity_type: str = Field(min_length=1, max_length=100)
    entity_id: str = Field(min_length=1, max_length=64)
    action: str = Field(min_length=1, max_length=50)
    actor_reference: str | None = Field(default=None, max_length=255)
    payload: dict[str, Any] | list[Any] | None = None
    occurred_at: datetime


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogRead(ORMBaseSchema, AuditLogBase):
    id: uuid.UUID
