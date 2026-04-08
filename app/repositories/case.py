from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.repositories.base import BaseRepository


class CaseRepository(BaseRepository[Case]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Case)
