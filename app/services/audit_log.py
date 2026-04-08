from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.audit_log import AuditLogRepository
from app.schemas.audit_log import AuditLogCreate
from app.services.base import BaseService


class AuditLogService(BaseService[AuditLog, AuditLogCreate, AuditLogCreate]):
    entity_name = "audit log"

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, repository=AuditLogRepository(session))

    async def create(self, payload: AuditLogCreate) -> AuditLog:
        return await super().create(payload)
