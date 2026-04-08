import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_canonical_field import CaseCanonicalField
from app.repositories.base import BaseRepository


class CaseCanonicalFieldRepository(BaseRepository[CaseCanonicalField]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=CaseCanonicalField)

    async def list_for_case(self, case_id: uuid.UUID) -> list[CaseCanonicalField]:
        result = await self.session.execute(
            select(CaseCanonicalField)
            .where(CaseCanonicalField.case_id == case_id)
            .order_by(CaseCanonicalField.field_key.asc())
        )
        return list(result.scalars().all())

    async def get_by_case_and_field_key(
        self,
        case_id: uuid.UUID,
        field_key: str,
    ) -> CaseCanonicalField | None:
        result = await self.session.execute(
            select(CaseCanonicalField).where(
                CaseCanonicalField.case_id == case_id,
                CaseCanonicalField.field_key == field_key,
            )
        )
        return result.scalars().first()
