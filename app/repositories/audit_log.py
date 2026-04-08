import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=AuditLog)

    async def list_for_case(self, case_id: uuid.UUID) -> list[AuditLog]:
        result = await self.session.execute(
            select(AuditLog).where(AuditLog.case_id == case_id).order_by(AuditLog.occurred_at.desc())
        )
        return list(result.scalars().all())
