import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.questionnaire import Questionnaire
from app.repositories.base import BaseRepository


class QuestionnaireRepository(BaseRepository[Questionnaire]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Questionnaire)

    async def get_latest_for_case(self, case_id: uuid.UUID) -> Questionnaire | None:
        result = await self.session.execute(
            select(Questionnaire)
            .options(selectinload(Questionnaire.template))
            .where(Questionnaire.case_id == case_id)
            .order_by(desc(Questionnaire.created_at))
        )
        return result.scalars().first()

    async def get_for_case_and_template(
        self,
        case_id: uuid.UUID,
        template_id: uuid.UUID,
    ) -> Questionnaire | None:
        result = await self.session.execute(
            select(Questionnaire)
            .where(
                Questionnaire.case_id == case_id,
                Questionnaire.template_id == template_id,
            )
            .order_by(desc(Questionnaire.created_at))
        )
        return result.scalars().first()
