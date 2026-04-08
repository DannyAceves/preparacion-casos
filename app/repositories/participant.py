from sqlalchemy.ext.asyncio import AsyncSession

from app.models.participant import Participant
from app.repositories.base import BaseRepository


class ParticipantRepository(BaseRepository[Participant]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Participant)
