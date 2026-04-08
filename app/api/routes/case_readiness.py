import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.case import CaseRead
from app.schemas.case_readiness import CaseReadinessRead, CaseReadinessValidateRequest, CaseTransitionRequest
from app.services.case_readiness import CaseReadinessService

router = APIRouter(prefix="/cases/{case_id}", tags=["case-readiness"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("/readiness", response_model=CaseReadinessRead)
async def get_case_readiness(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.VIEW_READINESS))],
) -> CaseReadinessRead:
    return await CaseReadinessService(session).get_readiness(case_id)


@router.post("/validate-readiness", response_model=CaseReadinessRead)
async def validate_case_readiness(
    case_id: uuid.UUID,
    payload: CaseReadinessValidateRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.VIEW_READINESS))],
) -> CaseReadinessRead:
    return await CaseReadinessService(session).validate_readiness(case_id, payload)


@router.post("/transition", response_model=CaseRead)
async def transition_case(
    case_id: uuid.UUID,
    payload: CaseTransitionRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.APPROVE_READINESS))],
) -> CaseRead:
    return await CaseReadinessService(session).transition_case(case_id, payload)
