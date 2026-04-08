import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_packet import CasePacket
from app.repositories.base import BaseRepository


class CasePacketRepository(BaseRepository[CasePacket]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=CasePacket)

    async def get_latest_for_case(self, case_id: uuid.UUID) -> CasePacket | None:
        result = await self.session.execute(
            select(CasePacket)
            .where(CasePacket.case_id == case_id)
            .order_by(CasePacket.packet_version.desc(), CasePacket.generated_at.desc())
        )
        return result.scalars().first()

    async def list_for_case(self, case_id: uuid.UUID) -> list[CasePacket]:
        result = await self.session.execute(
            select(CasePacket)
            .where(CasePacket.case_id == case_id)
            .order_by(CasePacket.packet_version.desc(), CasePacket.generated_at.desc())
        )
        return list(result.scalars().all())
