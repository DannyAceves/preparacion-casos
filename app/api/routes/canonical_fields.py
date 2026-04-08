import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.case_canonical_field import CaseCanonicalFieldPatchRequest, CaseCanonicalFieldRead
from app.services.case_canonical_field import CaseCanonicalFieldService

router = APIRouter(prefix="/cases/{case_id}/canonical-fields", tags=["canonical-fields"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("", response_model=list[CaseCanonicalFieldRead])
async def list_case_canonical_fields(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.VIEW_CANONICAL_FIELDS))],
) -> list[CaseCanonicalFieldRead]:
    return await CaseCanonicalFieldService(session).list_for_case(case_id)


@router.patch("/{field_key}", response_model=CaseCanonicalFieldRead)
async def upsert_case_canonical_field(
    case_id: uuid.UUID,
    field_key: str,
    payload: CaseCanonicalFieldPatchRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_CANONICAL_FIELDS))],
) -> CaseCanonicalFieldRead:
    return await CaseCanonicalFieldService(session).upsert_by_field_key(
        case_id=case_id,
        field_key=field_key,
        payload=payload,
    )
