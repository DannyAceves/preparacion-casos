from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.auth import SystemRole


class EmailLoginRequest(BaseModel):
    email: EmailStr


class AuthenticatedUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    role: SystemRole
    is_active: bool
