import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import require_permissions_for
from app.api.deps import get_session_dependency
from app.core.auth import SystemRole
from app.core.rbac import Permission
from app.schemas.system_user import (
    SystemUserCreate,
    SystemUserListFilters,
    SystemUserRead,
    SystemUserUpdate,
)
from app.services.system_user import SystemUserService

router = APIRouter(prefix="/admin/users", tags=["system-users"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("", response_model=list[SystemUserRead])
async def list_system_users(
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_USERS))],
    search: Annotated[str | None, Query(max_length=255)] = None,
    role: SystemRole | None = None,
    is_active: bool | None = None,
) -> list[SystemUserRead]:
    return await SystemUserService(session).list_filtered(
        SystemUserListFilters(search=search, role=role, is_active=is_active)
    )


@router.post("", response_model=SystemUserRead, status_code=status.HTTP_201_CREATED)
async def create_system_user(
    payload: SystemUserCreate,
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_USERS))],
) -> SystemUserRead:
    return await SystemUserService(session).create(payload)


@router.get("/{user_id}", response_model=SystemUserRead)
async def get_system_user(
    user_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_USERS))],
) -> SystemUserRead:
    return await SystemUserService(session).get(user_id)


@router.patch("/{user_id}", response_model=SystemUserRead)
async def update_system_user(
    user_id: uuid.UUID,
    payload: SystemUserUpdate,
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_USERS))],
) -> SystemUserRead:
    return await SystemUserService(session).update(user_id, payload)
