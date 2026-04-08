import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.case_questionnaire import (
    CaseQuestionnaireAnswerUpdateRequest,
    CaseQuestionnaireAnswersUpsertRequest,
    CaseQuestionnaireRead,
    QuestionnaireAnswerRead,
)
from app.services.case_questionnaire import CaseQuestionnaireService

router = APIRouter(prefix="/cases/{case_id}/questionnaire", tags=["case-questionnaire"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("", response_model=CaseQuestionnaireRead)
async def get_case_questionnaire(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.VIEW_QUESTIONNAIRES))],
) -> CaseQuestionnaireRead:
    return await CaseQuestionnaireService(session).get_case_questionnaire(case_id)


@router.post("/answers", response_model=list[QuestionnaireAnswerRead], status_code=status.HTTP_201_CREATED)
async def upsert_case_questionnaire_answers(
    case_id: uuid.UUID,
    payload: CaseQuestionnaireAnswersUpsertRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_QUESTIONNAIRES))],
) -> list[QuestionnaireAnswerRead]:
    return await CaseQuestionnaireService(session).upsert_answers(case_id, payload)


@router.patch("/answers/{answer_id}", response_model=QuestionnaireAnswerRead)
async def update_case_questionnaire_answer(
    case_id: uuid.UUID,
    answer_id: uuid.UUID,
    payload: CaseQuestionnaireAnswerUpdateRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_QUESTIONNAIRES))],
) -> QuestionnaireAnswerRead:
    return await CaseQuestionnaireService(session).update_answer(case_id, answer_id, payload)
