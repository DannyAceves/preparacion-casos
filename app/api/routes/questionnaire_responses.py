import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import require_permissions_for
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.questionnaire_response import (
    QuestionnaireResponseCreate,
    QuestionnaireResponseRead,
    QuestionnaireResponseUpdate,
)
from app.services.questionnaire_response import QuestionnaireResponseService

router = APIRouter(
    prefix="/questionnaire-responses",
    tags=["questionnaire-responses"],
    dependencies=[Depends(require_permissions_for(Permission.MANAGE_TEMPLATES))],
)
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("", response_model=list[QuestionnaireResponseRead])
async def list_questionnaire_responses(session: SessionDep) -> list[QuestionnaireResponseRead]:
    return await QuestionnaireResponseService(session).list()


@router.post("", response_model=QuestionnaireResponseRead, status_code=status.HTTP_201_CREATED)
async def create_questionnaire_response(
    payload: QuestionnaireResponseCreate,
    session: SessionDep,
) -> QuestionnaireResponseRead:
    return await QuestionnaireResponseService(session).create(payload)


@router.get("/{response_id}", response_model=QuestionnaireResponseRead)
async def get_questionnaire_response(response_id: uuid.UUID, session: SessionDep) -> QuestionnaireResponseRead:
    return await QuestionnaireResponseService(session).get(response_id)


@router.patch("/{response_id}", response_model=QuestionnaireResponseRead)
async def update_questionnaire_response(
    response_id: uuid.UUID,
    payload: QuestionnaireResponseUpdate,
    session: SessionDep,
) -> QuestionnaireResponseRead:
    return await QuestionnaireResponseService(session).update(response_id, payload)


@router.delete("/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_questionnaire_response(response_id: uuid.UUID, session: SessionDep) -> Response:
    await QuestionnaireResponseService(session).delete(response_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
