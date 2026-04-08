from sqlalchemy.ext.asyncio import AsyncSession

from app.models.questionnaire_response import QuestionnaireResponse
from app.repositories.base import BaseRepository


class QuestionnaireResponseRepository(BaseRepository[QuestionnaireResponse]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=QuestionnaireResponse)
