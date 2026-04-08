from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session_dependency
from app.schemas.auth import AuthenticatedUserRead, EmailLoginRequest
from app.services.system_user import SystemUserService

router = APIRouter(prefix="/auth", tags=["auth"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.post("/login", response_model=AuthenticatedUserRead)
async def login_with_email(
    payload: EmailLoginRequest,
    session: SessionDep,
) -> AuthenticatedUserRead:
    user = await SystemUserService(session).authenticate_by_email(payload.email)
    return AuthenticatedUserRead(
        id=str(user.id),
        email=user.email,
        full_name=f"{user.first_name} {user.last_name}".strip(),
        role=user.role,
        is_active=user.is_active,
    )
