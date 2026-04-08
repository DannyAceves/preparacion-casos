from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session_dependency
from app.core.auth import AuthenticatedPrincipal, get_current_principal
from app.core.rbac import AuthorizationService, Permission, principal_has_permission, require_permissions

SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]
PrincipalDep = Annotated[AuthenticatedPrincipal, Depends(get_current_principal)]


def require_permission(permission: Permission) -> Callable[..., AuthenticatedPrincipal]:
    async def dependency(principal: PrincipalDep) -> AuthenticatedPrincipal:
        require_permissions(principal, permission)
        return principal

    return dependency


def require_permissions_for(*permissions: Permission) -> Callable[..., AuthenticatedPrincipal]:
    async def dependency(principal: PrincipalDep) -> AuthenticatedPrincipal:
        require_permissions(principal, *permissions)
        return principal

    return dependency


def require_any_permission(*permissions: Permission) -> Callable[..., AuthenticatedPrincipal]:
    async def dependency(principal: PrincipalDep) -> AuthenticatedPrincipal:
        if not any(principal_has_permission(principal, permission) for permission in permissions):
            require_permissions(principal, permissions[0])
        return principal

    return dependency


def authorize_case_access(*permissions: Permission) -> Callable[..., AuthenticatedPrincipal]:
    async def dependency(
        case_id: uuid.UUID,
        session: SessionDep,
        principal: PrincipalDep,
    ) -> AuthenticatedPrincipal:
        require_permissions(principal, *permissions)
        await AuthorizationService(session).authorize_case_access(principal, case_id)
        return principal

    return dependency


def authorize_consultation_access(*permissions: Permission) -> Callable[..., AuthenticatedPrincipal]:
    async def dependency(
        consultation_id: uuid.UUID,
        session: SessionDep,
        principal: PrincipalDep,
    ) -> AuthenticatedPrincipal:
        require_permissions(principal, *permissions)
        await AuthorizationService(session).authorize_consultation_access(principal, consultation_id)
        return principal

    return dependency


def authorize_consultation_access_any(*permissions: Permission) -> Callable[..., AuthenticatedPrincipal]:
    async def dependency(
        consultation_id: uuid.UUID,
        session: SessionDep,
        principal: PrincipalDep,
    ) -> AuthenticatedPrincipal:
        if not any(principal_has_permission(principal, permission) for permission in permissions):
            require_permissions(principal, permissions[0])
        await AuthorizationService(session).authorize_consultation_access(principal, consultation_id)
        return principal

    return dependency


def authorize_client_access(*permissions: Permission) -> Callable[..., AuthenticatedPrincipal]:
    async def dependency(
        client_id: uuid.UUID,
        session: SessionDep,
        principal: PrincipalDep,
    ) -> AuthenticatedPrincipal:
        require_permissions(principal, *permissions)
        await AuthorizationService(session).authorize_client_access(principal, client_id)
        return principal

    return dependency


def authorize_document_access(*permissions: Permission) -> Callable[..., AuthenticatedPrincipal]:
    async def dependency(
        document_id: uuid.UUID,
        session: SessionDep,
        principal: PrincipalDep,
    ) -> AuthenticatedPrincipal:
        require_permissions(principal, *permissions)
        await AuthorizationService(session).authorize_document_access(principal, document_id)
        return principal

    return dependency


def authorize_generated_form_access(*permissions: Permission) -> Callable[..., AuthenticatedPrincipal]:
    async def dependency(
        generated_form_id: uuid.UUID,
        session: SessionDep,
        principal: PrincipalDep,
    ) -> AuthenticatedPrincipal:
        require_permissions(principal, *permissions)
        await AuthorizationService(session).authorize_generated_form_access(principal, generated_form_id)
        return principal

    return dependency


def authorize_participant_access(*permissions: Permission) -> Callable[..., AuthenticatedPrincipal]:
    async def dependency(
        participant_id: uuid.UUID,
        session: SessionDep,
        principal: PrincipalDep,
    ) -> AuthenticatedPrincipal:
        require_permissions(principal, *permissions)
        await AuthorizationService(session).authorize_participant_access(principal, participant_id)
        return principal

    return dependency
