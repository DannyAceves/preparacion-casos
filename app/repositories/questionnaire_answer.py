import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.questionnaire_answer import QuestionnaireAnswer
from app.repositories.base import BaseRepository


class QuestionnaireAnswerRepository(BaseRepository[QuestionnaireAnswer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=QuestionnaireAnswer)

    async def list_for_case(self, case_id: uuid.UUID) -> list[QuestionnaireAnswer]:
        result = await self.session.execute(
            select(QuestionnaireAnswer).where(QuestionnaireAnswer.case_id == case_id)
        )
        return list(result.scalars().all())

    async def get_for_case_and_question(
        self,
        case_id: uuid.UUID,
        question_id: uuid.UUID,
    ) -> QuestionnaireAnswer | None:
        result = await self.session.execute(
            select(QuestionnaireAnswer).where(
                QuestionnaireAnswer.case_id == case_id,
                QuestionnaireAnswer.question_id == question_id,
            )
        )
        return result.scalars().first()

    async def get_for_case_by_id(
        self,
        case_id: uuid.UUID,
        answer_id: uuid.UUID,
    ) -> QuestionnaireAnswer | None:
        result = await self.session.execute(
            select(QuestionnaireAnswer).where(
                QuestionnaireAnswer.case_id == case_id,
                QuestionnaireAnswer.id == answer_id,
            )
        )
        return result.scalars().first()
