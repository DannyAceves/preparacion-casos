import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.questionnaire import Questionnaire
from app.models.questionnaire_response import QuestionnaireResponse
from app.repositories.questionnaire_response import QuestionnaireResponseRepository
from app.schemas.questionnaire_response import QuestionnaireResponseCreate, QuestionnaireResponseUpdate
from app.services.base import BaseService


class QuestionnaireResponseService(
    BaseService[QuestionnaireResponse, QuestionnaireResponseCreate, QuestionnaireResponseUpdate]
):
    entity_name = "questionnaire response"

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, repository=QuestionnaireResponseRepository(session))

    async def create(self, payload: QuestionnaireResponseCreate) -> QuestionnaireResponse:
        await self.ensure_exists(Questionnaire, payload.questionnaire_id, "questionnaire")
        return await super().create(payload)

    async def update(
        self,
        entity_id: uuid.UUID,
        payload: QuestionnaireResponseUpdate,
    ) -> QuestionnaireResponse:
        if payload.questionnaire_id is not None:
            await self.ensure_exists(Questionnaire, payload.questionnaire_id, "questionnaire")
        return await super().update(entity_id, payload)
