import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.inconsistency import InconsistencyActionRequest, InconsistencyCreateRequest, InconsistencyRead
from app.services.inconsistency import InconsistencyService

router = APIRouter(prefix="/cases/{case_id}/inconsistencies", tags=["inconsistencies"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("", response_model=list[InconsistencyRead])
async def list_case_inconsistencies(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.VIEW_INCONSISTENCIES))],
) -> list[InconsistencyRead]:
    return await InconsistencyService(session).list_for_case(case_id)


@router.post("", response_model=InconsistencyRead, status_code=status.HTTP_201_CREATED)
async def create_case_inconsistency(
    case_id: uuid.UUID,
    payload: InconsistencyCreateRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.VIEW_INCONSISTENCIES))],
) -> InconsistencyRead:
    return await InconsistencyService(session).create_for_case(case_id, payload)


@router.post("/{inconsistency_id}/resolve", response_model=InconsistencyRead)
async def resolve_case_inconsistency(
    case_id: uuid.UUID,
    inconsistency_id: uuid.UUID,
    payload: InconsistencyActionRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.RESOLVE_INCONSISTENCIES))],
) -> InconsistencyRead:
    return await InconsistencyService(session).resolve_for_case(case_id, inconsistency_id, payload)


@router.post("/{inconsistency_id}/dismiss", response_model=InconsistencyRead)
async def dismiss_case_inconsistency(
    case_id: uuid.UUID,
    inconsistency_id: uuid.UUID,
    payload: InconsistencyActionRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.RESOLVE_INCONSISTENCIES))],
) -> InconsistencyRead:
    return await InconsistencyService(session).dismiss_for_case(case_id, inconsistency_id, payload)
