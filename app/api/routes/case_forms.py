import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.generated_form import GenerateFormsRequest, GeneratedFormRead
from app.services.generated_form import GeneratedFormService

router = APIRouter(prefix="/cases/{case_id}/forms", tags=["case-forms"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.post("/generate", response_model=list[GeneratedFormRead], status_code=status.HTTP_201_CREATED)
async def generate_case_forms(
    case_id: uuid.UUID,
    payload: GenerateFormsRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_FORMS))],
) -> list[GeneratedFormRead]:
    return await GeneratedFormService(session).generate_for_case(case_id, payload)


@router.get("", response_model=list[GeneratedFormRead])
async def list_case_forms(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_FORMS))],
) -> list[GeneratedFormRead]:
    return await GeneratedFormService(session).list_for_case(case_id)
