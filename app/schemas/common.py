import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(ORMBaseSchema):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
