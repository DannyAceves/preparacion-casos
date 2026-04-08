import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_portal import ClientPortalAccess
from app.repositories.base import BaseRepository


class ClientPortalAccessRepository(BaseRepository[ClientPortalAccess]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=ClientPortalAccess)

    async def get_for_case(self, case_id: uuid.UUID) -> ClientPortalAccess | None:
        result = await self.session.execute(
            select(ClientPortalAccess).where(ClientPortalAccess.case_id == case_id)
        )
        return result.scalar_one_or_none()

    async def get_by_token_hash(self, token_hash: str) -> ClientPortalAccess | None:
        result = await self.session.execute(
            select(ClientPortalAccess).where(ClientPortalAccess.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_session_hash(self, session_hash: str) -> ClientPortalAccess | None:
        result = await self.session.execute(
            select(ClientPortalAccess).where(ClientPortalAccess.access_session_hash == session_hash)
        )
        return result.scalar_one_or_none()
