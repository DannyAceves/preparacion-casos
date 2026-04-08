import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access, require_permissions_for
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.case import CaseCreate, CaseRead, CaseUpdate
from app.services.case import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("", response_model=list[CaseRead])
async def list_cases(
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.VIEW_CASES))],
) -> list[CaseRead]:
    return await CaseService(session).list()


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_CASES))],
) -> CaseRead:
    return await CaseService(session).create(payload)


@router.get("/{case_id}", response_model=CaseRead)
async def get_case(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.VIEW_CASES))],
) -> CaseRead:
    return await CaseService(session).get(case_id)


@router.patch("/{case_id}", response_model=CaseRead)
async def update_case(
    case_id: uuid.UUID,
    payload: CaseUpdate,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_CASES))],
) -> CaseRead:
    return await CaseService(session).update(case_id, payload)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_USERS))],
) -> Response:
    await CaseService(session).delete(case_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
