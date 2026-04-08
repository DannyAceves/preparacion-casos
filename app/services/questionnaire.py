import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.questionnaire import Questionnaire
from app.repositories.questionnaire import QuestionnaireRepository
from app.schemas.questionnaire import QuestionnaireCreate, QuestionnaireUpdate
from app.services.base import BaseService


class QuestionnaireService(BaseService[Questionnaire, QuestionnaireCreate, QuestionnaireUpdate]):
    entity_name = "questionnaire"

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, repository=QuestionnaireRepository(session))

    async def create(self, payload: QuestionnaireCreate) -> Questionnaire:
        await self.ensure_exists(Case, payload.case_id, "case")
        return await super().create(payload)

    async def update(self, entity_id: uuid.UUID, payload: QuestionnaireUpdate) -> Questionnaire:
        if payload.case_id is not None:
            await self.ensure_exists(Case, payload.case_id, "case")
        return await super().update(entity_id, payload)
