import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Review)

    async def list_for_case(self, case_id: uuid.UUID) -> list[Review]:
        result = await self.session.execute(
            select(Review).where(Review.case_id == case_id).order_by(Review.reviewed_at.desc(), Review.created_at.desc())
        )
        return list(result.scalars().all())
