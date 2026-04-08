import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.review import CaseReviewCreateRequest, ReviewRead, TimelineEventRead
from app.services.review import ReviewService

router = APIRouter(prefix="/cases/{case_id}", tags=["reviews"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.post("/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_case_review(
    case_id: uuid.UUID,
    payload: CaseReviewCreateRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.CREATE_REVIEWS))],
) -> ReviewRead:
    return await ReviewService(session).create_for_case(case_id, payload)


@router.get("/reviews", response_model=list[ReviewRead])
async def list_case_reviews(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.VIEW_REVIEWS))],
) -> list[ReviewRead]:
    return await ReviewService(session).list_for_case(case_id)


@router.get("/timeline", response_model=list[TimelineEventRead])
async def get_case_timeline(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.VIEW_REVIEWS))],
) -> list[TimelineEventRead]:
    return await ReviewService(session).get_case_timeline(case_id)
