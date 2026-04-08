from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.auth import AuthenticatedPrincipal, SystemRole
from app.core.rbac import AuthorizationService, Permission, principal_has_permission, require_permissions
from app.models.case import Case
from app.models.client import Client


class FakeSession:
    def __init__(self, entities: dict[tuple[type[object], uuid.UUID], object]) -> None:
        self.entities = entities

    async def get(self, model: type[object], entity_id: uuid.UUID) -> object | None:
        return self.entities.get((model, entity_id))


def build_principal(
    *roles: SystemRole,
    subject: str = "user-1",
    client_id: uuid.UUID | None = None,
    assigned_case_ids: set[uuid.UUID] | None = None,
) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        subject=subject,
        roles=frozenset(roles),
        client_id=client_id,
        assigned_case_ids=frozenset(assigned_case_ids or set()),
    )


def test_permission_matrix_blocks_paralegal_from_submission_approval() -> None:
    paralegal = build_principal(SystemRole.PARALEGAL)

    assert principal_has_permission(paralegal, Permission.EXECUTE_SUBMISSIONS) is True
    assert principal_has_permission(paralegal, Permission.APPROVE_SUBMISSIONS) is False

    with pytest.raises(HTTPException) as exc:
        require_permissions(paralegal, Permission.APPROVE_SUBMISSIONS)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_authorize_case_access_respects_assigned_case_ids_for_attorney() -> None:
    allowed_case_id = uuid.uuid4()
    blocked_case_id = uuid.uuid4()
    client_id = uuid.uuid4()
    session = FakeSession(
        {
            (Case, allowed_case_id): SimpleNamespace(id=allowed_case_id, client_id=client_id),
            (Case, blocked_case_id): SimpleNamespace(id=blocked_case_id, client_id=client_id),
        }
    )
    service = AuthorizationService(session)
    attorney = build_principal(SystemRole.ATTORNEY, assigned_case_ids={allowed_case_id})

    authorized_case = await service.authorize_case_access(attorney, allowed_case_id)

    assert authorized_case.id == allowed_case_id

    with pytest.raises(HTTPException) as exc:
        await service.authorize_case_access(attorney, blocked_case_id)

    assert exc.value.status_code == 403
    assert exc.value.detail == "case is not assigned"


@pytest.mark.asyncio
async def test_authorize_client_access_blocks_other_clients() -> None:
    allowed_client_id = uuid.uuid4()
    blocked_client_id = uuid.uuid4()
    session = FakeSession(
        {
            (Client, allowed_client_id): SimpleNamespace(id=allowed_client_id),
            (Client, blocked_client_id): SimpleNamespace(id=blocked_client_id),
        }
    )
    service = AuthorizationService(session)
    principal = build_principal(SystemRole.CLIENT, client_id=allowed_client_id)

    client = await service.authorize_client_access(principal, allowed_client_id)

    assert client.id == allowed_client_id

    with pytest.raises(HTTPException) as exc:
        await service.authorize_client_access(principal, blocked_client_id)

    assert exc.value.status_code == 403
    assert exc.value.detail == "client access denied"
