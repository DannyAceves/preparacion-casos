import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import require_permissions_for
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.audit_log import AuditLogCreate, AuditLogRead
from app.services.audit_log import AuditLogService

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit-logs"],
    dependencies=[Depends(require_permissions_for(Permission.VIEW_AUDIT_LOGS))],
)
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("", response_model=list[AuditLogRead])
async def list_audit_logs(session: SessionDep) -> list[AuditLogRead]:
    return await AuditLogService(session).list()


@router.post("", response_model=AuditLogRead, status_code=status.HTTP_201_CREATED)
async def create_audit_log(payload: AuditLogCreate, session: SessionDep) -> AuditLogRead:
    return await AuditLogService(session).create(payload)


@router.get("/{audit_log_id}", response_model=AuditLogRead)
async def get_audit_log(audit_log_id: uuid.UUID, session: SessionDep) -> AuditLogRead:
    return await AuditLogService(session).get(audit_log_id)


@router.delete("/{audit_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit_log(audit_log_id: uuid.UUID, session: SessionDep) -> Response:
    await AuditLogService(session).delete(audit_log_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
