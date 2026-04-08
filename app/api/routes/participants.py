import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_participant_access, require_permissions_for
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.participant import ParticipantCreate, ParticipantRead, ParticipantUpdate
from app.services.participant import ParticipantService

router = APIRouter(prefix="/participants", tags=["participants"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("", response_model=list[ParticipantRead])
async def list_participants(
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_CASE_ASSIGNMENTS))],
) -> list[ParticipantRead]:
    return await ParticipantService(session).list()


@router.post("", response_model=ParticipantRead, status_code=status.HTTP_201_CREATED)
async def create_participant(
    payload: ParticipantCreate,
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_CASE_ASSIGNMENTS))],
) -> ParticipantRead:
    return await ParticipantService(session).create(payload)


@router.get("/{participant_id}", response_model=ParticipantRead)
async def get_participant(
    participant_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_participant_access(Permission.MANAGE_CASE_ASSIGNMENTS))],
) -> ParticipantRead:
    return await ParticipantService(session).get(participant_id)


@router.patch("/{participant_id}", response_model=ParticipantRead)
async def update_participant(
    participant_id: uuid.UUID,
    payload: ParticipantUpdate,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_participant_access(Permission.MANAGE_CASE_ASSIGNMENTS))],
) -> ParticipantRead:
    return await ParticipantService(session).update(participant_id, payload)


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_participant(
    participant_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_participant_access(Permission.MANAGE_CASE_ASSIGNMENTS))],
) -> Response:
    await ParticipantService(session).delete(participant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
