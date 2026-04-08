import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_generated_form_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.generated_form import (
    AssistedFormFieldUpdateRequest,
    AssistedFormWorkspaceRead,
    GeneratedFormDetailRead,
    GeneratedFormRead,
    GeneratedFormReviewRequest,
)
from app.services.generated_form import GeneratedFormService

router = APIRouter(prefix="/generated-forms", tags=["generated-forms"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("/{generated_form_id}", response_model=GeneratedFormDetailRead)
async def get_generated_form(
    generated_form_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_generated_form_access(Permission.MANAGE_FORMS))],
) -> GeneratedFormDetailRead:
    return await GeneratedFormService(session).get_detail(generated_form_id)


@router.get("/{generated_form_id}/workspace", response_model=AssistedFormWorkspaceRead)
async def get_generated_form_workspace(
    generated_form_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_generated_form_access(Permission.MANAGE_FORMS))],
) -> AssistedFormWorkspaceRead:
    return await GeneratedFormService(session).get_workspace(generated_form_id)


@router.patch("/{generated_form_id}/workspace/fields/{form_field_key:path}", response_model=GeneratedFormDetailRead)
async def update_generated_form_workspace_field(
    generated_form_id: uuid.UUID,
    form_field_key: str,
    payload: AssistedFormFieldUpdateRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_generated_form_access(Permission.MANAGE_FORMS))],
) -> GeneratedFormDetailRead:
    return await GeneratedFormService(session).update_workspace_field(generated_form_id, form_field_key, payload)


@router.post("/{generated_form_id}/approve", response_model=GeneratedFormRead)
async def approve_generated_form(
    generated_form_id: uuid.UUID,
    payload: GeneratedFormReviewRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_generated_form_access(Permission.APPROVE_FORMS))],
) -> GeneratedFormRead:
    return await GeneratedFormService(session).approve(generated_form_id, payload)


@router.post("/{generated_form_id}/fix", response_model=GeneratedFormRead)
async def mark_generated_form_fix_required(
    generated_form_id: uuid.UUID,
    payload: GeneratedFormReviewRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_generated_form_access(Permission.APPROVE_FORMS))],
) -> GeneratedFormRead:
    return await GeneratedFormService(session).mark_fix_required(generated_form_id, payload)
