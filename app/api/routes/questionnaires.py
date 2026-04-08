import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import require_permissions_for
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.questionnaire import QuestionnaireCreate, QuestionnaireRead, QuestionnaireUpdate
from app.services.questionnaire import QuestionnaireService

router = APIRouter(
    prefix="/questionnaires",
    tags=["questionnaires"],
    dependencies=[Depends(require_permissions_for(Permission.MANAGE_TEMPLATES))],
)
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("", response_model=list[QuestionnaireRead])
async def list_questionnaires(session: SessionDep) -> list[QuestionnaireRead]:
    return await QuestionnaireService(session).list()


@router.post("", response_model=QuestionnaireRead, status_code=status.HTTP_201_CREATED)
async def create_questionnaire(
    payload: QuestionnaireCreate,
    session: SessionDep,
) -> QuestionnaireRead:
    return await QuestionnaireService(session).create(payload)


@router.get("/{questionnaire_id}", response_model=QuestionnaireRead)
async def get_questionnaire(questionnaire_id: uuid.UUID, session: SessionDep) -> QuestionnaireRead:
    return await QuestionnaireService(session).get(questionnaire_id)


@router.patch("/{questionnaire_id}", response_model=QuestionnaireRead)
async def update_questionnaire(
    questionnaire_id: uuid.UUID,
    payload: QuestionnaireUpdate,
    session: SessionDep,
) -> QuestionnaireRead:
    return await QuestionnaireService(session).update(questionnaire_id, payload)


@router.delete("/{questionnaire_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_questionnaire(questionnaire_id: uuid.UUID, session: SessionDep) -> Response:
    await QuestionnaireService(session).delete(questionnaire_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
