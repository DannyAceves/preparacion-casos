from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.auth import SystemRole
from app.schemas.common import TimestampedSchema


class SystemUserBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    role: SystemRole
    is_active: bool = True


class SystemUserCreate(SystemUserBase):
    pass


class SystemUserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    role: SystemRole | None = None
    is_active: bool | None = None


class SystemUserRead(TimestampedSchema, SystemUserBase):
    last_login_at: datetime | None = None


class SystemUserListFilters(BaseModel):
    search: str | None = Field(default=None, max_length=255)
    role: SystemRole | None = None
    is_active: bool | None = None
