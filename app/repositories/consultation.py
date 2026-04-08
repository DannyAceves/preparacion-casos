from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import Consultation
from app.repositories.base import BaseRepository


class ConsultationRepository(BaseRepository[Consultation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Consultation)
