import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import (
    authorize_consultation_access,
    authorize_consultation_access_any,
    require_any_permission,
    require_permissions_for,
)
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.consultation import (
    ConsultationConversionResult,
    ConsultationConvertToCaseRequest,
    ConsultationCreate,
    ConsultationRead,
    ConsultationUpdate,
)
from app.services.consultation import ConsultationService

router = APIRouter(prefix="/consultations", tags=["consultations"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("", response_model=list[ConsultationRead])
async def list_consultations(
    session: SessionDep,
    _: Annotated[object, Depends(require_any_permission(Permission.MANAGE_INTAKE, Permission.CONVERT_CONSULTATION))],
) -> list[ConsultationRead]:
    return await ConsultationService(session).list()


@router.post("", response_model=ConsultationRead, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    payload: ConsultationCreate,
    session: SessionDep,
    _: Annotated[object, Depends(require_permissions_for(Permission.MANAGE_INTAKE))],
) -> ConsultationRead:
    return await ConsultationService(session).create(payload)


@router.get("/{consultation_id}", response_model=ConsultationRead)
async def get_consultation(
    consultation_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_consultation_access_any(Permission.MANAGE_INTAKE, Permission.CONVERT_CONSULTATION))],
) -> ConsultationRead:
    return await ConsultationService(session).get(consultation_id)


@router.patch("/{consultation_id}", response_model=ConsultationRead)
async def update_consultation(
    consultation_id: uuid.UUID,
    payload: ConsultationUpdate,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_consultation_access(Permission.MANAGE_INTAKE))],
) -> ConsultationRead:
    return await ConsultationService(session).update(consultation_id, payload)


@router.post("/{consultation_id}/convert", response_model=ConsultationConversionResult)
async def convert_consultation_to_case(
    consultation_id: uuid.UUID,
    payload: ConsultationConvertToCaseRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_consultation_access(Permission.CONVERT_CONSULTATION))],
) -> ConsultationConversionResult:
    return await ConsultationService(session).convert_to_case(consultation_id, payload)
