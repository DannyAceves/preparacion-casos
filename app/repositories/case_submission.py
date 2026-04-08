import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_submission import CaseSubmission
from app.repositories.base import BaseRepository


class CaseSubmissionRepository(BaseRepository[CaseSubmission]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=CaseSubmission)

    async def get_for_case(self, case_id: uuid.UUID) -> CaseSubmission | None:
        result = await self.session.execute(
            select(CaseSubmission).where(CaseSubmission.case_id == case_id)
        )
        return result.scalars().first()
