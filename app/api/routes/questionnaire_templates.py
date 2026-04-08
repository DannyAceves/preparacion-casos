import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access, require_permissions_for
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.questionnaire import QuestionnaireRead
from app.schemas.questionnaire_template_builder import (
    QuestionnaireInstanceCreate,
    QuestionnaireTemplateBuilderCreate,
    QuestionnaireTemplateBuilderRead,
    QuestionnaireTemplateBuilderUpdate,
    QuestionnaireTemplateVersionCreate,
)
from app.services.questionnaire_template_builder import QuestionnaireTemplateBuilderService

router = APIRouter(tags=["questionnaire-templates"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("/questionnaire-templates", response_model=list[QuestionnaireTemplateBuilderRead])
async def list_questionnaire_templates(
    session: SessionDep,
    case_type: Annotated[str | None, Query()] = None,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_TEMPLATES))] = None,
) -> list[QuestionnaireTemplateBuilderRead]:
    return await QuestionnaireTemplateBuilderService(session).list_templates(case_type)


@router.post("/questionnaire-templates", response_model=QuestionnaireTemplateBuilderRead, status_code=status.HTTP_201_CREATED)
async def create_questionnaire_template(
    payload: QuestionnaireTemplateBuilderCreate,
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_TEMPLATES))],
) -> QuestionnaireTemplateBuilderRead:
    return await QuestionnaireTemplateBuilderService(session).create_template(payload)


@router.get("/questionnaire-templates/{template_id}", response_model=QuestionnaireTemplateBuilderRead)
async def get_questionnaire_template(
    template_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_TEMPLATES))],
) -> QuestionnaireTemplateBuilderRead:
    return await QuestionnaireTemplateBuilderService(session).get_template(template_id)


@router.patch("/questionnaire-templates/{template_id}", response_model=QuestionnaireTemplateBuilderRead)
async def update_questionnaire_template(
    template_id: uuid.UUID,
    payload: QuestionnaireTemplateBuilderUpdate,
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_TEMPLATES))],
) -> QuestionnaireTemplateBuilderRead:
    return await QuestionnaireTemplateBuilderService(session).update_template(template_id, payload)


@router.post("/questionnaire-templates/{template_id}/activate", response_model=QuestionnaireTemplateBuilderRead)
async def activate_questionnaire_template(
    template_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_TEMPLATES))],
) -> QuestionnaireTemplateBuilderRead:
    return await QuestionnaireTemplateBuilderService(session).activate_template(template_id)


@router.post(
    "/questionnaire-templates/{template_id}/versions",
    response_model=QuestionnaireTemplateBuilderRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_questionnaire_template_version(
    template_id: uuid.UUID,
    payload: QuestionnaireTemplateVersionCreate,
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_TEMPLATES))],
) -> QuestionnaireTemplateBuilderRead:
    return await QuestionnaireTemplateBuilderService(session).create_new_version(template_id, payload)


@router.post(
    "/cases/{case_id}/questionnaire/instantiate",
    response_model=QuestionnaireRead,
    status_code=status.HTTP_201_CREATED,
)
async def instantiate_case_questionnaire(
    case_id: uuid.UUID,
    payload: QuestionnaireInstanceCreate,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_QUESTIONNAIRES))],
) -> QuestionnaireRead:
    return await QuestionnaireTemplateBuilderService(session).instantiate_for_case(case_id, payload)
