import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.case_packet import CasePacketGenerateRequest, CasePacketRead
from app.services.case_packet import CasePacketService

router = APIRouter(prefix="/cases/{case_id}/packet", tags=["case-packets"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.post("/generate", response_model=CasePacketRead, status_code=status.HTTP_201_CREATED)
async def generate_case_packet(
    case_id: uuid.UUID,
    payload: CasePacketGenerateRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_PACKETS))],
) -> CasePacketRead:
    return await CasePacketService(session).generate_for_case(case_id, payload)


@router.get("", response_model=CasePacketRead)
async def get_case_packet(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_PACKETS))],
) -> CasePacketRead:
    return await CasePacketService(session).get_latest_for_case(case_id)
