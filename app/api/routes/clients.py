import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_client_access, require_permissions_for
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.services.client import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("", response_model=list[ClientRead])
async def list_clients(
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.VIEW_CLIENTS))],
) -> list[ClientRead]:
    return await ClientService(session).list()


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientCreate,
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_CLIENTS))],
) -> ClientRead:
    return await ClientService(session).create(payload)


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_client_access(Permission.VIEW_CLIENTS))],
) -> ClientRead:
    return await ClientService(session).get(client_id)


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: uuid.UUID,
    payload: ClientUpdate,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_client_access(Permission.MANAGE_CLIENTS))],
) -> ClientRead:
    return await ClientService(session).update(client_id, payload)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_client_access(Permission.MANAGE_USERS))],
) -> Response:
    await ClientService(session).delete(client_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
