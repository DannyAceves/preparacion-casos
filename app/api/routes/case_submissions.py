import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.case import CaseRead
from app.schemas.case_submission import (
    CaseCloseRequest,
    CaseSubmissionApproveRequest,
    CaseSubmissionFailRequest,
    CaseSubmissionRead,
    CaseSubmissionSubmitRequest,
)
from app.services.case_submission import CaseSubmissionService

router = APIRouter(prefix="/cases/{case_id}", tags=["case-submissions"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.post("/submission/approve", response_model=CaseSubmissionRead)
async def approve_case_submission(
    case_id: uuid.UUID,
    payload: CaseSubmissionApproveRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.APPROVE_SUBMISSIONS))],
) -> CaseSubmissionRead:
    return await CaseSubmissionService(session).approve_for_submission(case_id, payload)


@router.post("/submission/submit", response_model=CaseSubmissionRead)
async def submit_case(
    case_id: uuid.UUID,
    payload: CaseSubmissionSubmitRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.EXECUTE_SUBMISSIONS))],
) -> CaseSubmissionRead:
    return await CaseSubmissionService(session).submit(case_id, payload)


@router.post("/submission/fail", response_model=CaseSubmissionRead)
async def fail_case_submission(
    case_id: uuid.UUID,
    payload: CaseSubmissionFailRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.EXECUTE_SUBMISSIONS))],
) -> CaseSubmissionRead:
    return await CaseSubmissionService(session).fail(case_id, payload)


@router.post("/close", response_model=CaseRead)
async def close_case(
    case_id: uuid.UUID,
    payload: CaseCloseRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.APPROVE_SUBMISSIONS))],
) -> CaseRead:
    return await CaseSubmissionService(session).close_case(case_id, payload)


@router.get("/submission", response_model=CaseSubmissionRead)
async def get_case_submission(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.VIEW_SUBMISSIONS))],
) -> CaseSubmissionRead:
    return await CaseSubmissionService(session).get_for_case(case_id)
