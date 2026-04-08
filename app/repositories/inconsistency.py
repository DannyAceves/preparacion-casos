import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inconsistency import Inconsistency
from app.repositories.base import BaseRepository


class InconsistencyRepository(BaseRepository[Inconsistency]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Inconsistency)

    async def list_for_case(self, case_id: uuid.UUID) -> list[Inconsistency]:
        result = await self.session.execute(
            select(Inconsistency)
            .where(Inconsistency.case_id == case_id)
            .order_by(Inconsistency.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_case(
        self,
        case_id: uuid.UUID,
        inconsistency_id: uuid.UUID,
    ) -> Inconsistency | None:
        result = await self.session.execute(
            select(Inconsistency).where(
                Inconsistency.case_id == case_id,
                Inconsistency.id == inconsistency_id,
            )
        )
        return result.scalars().first()
