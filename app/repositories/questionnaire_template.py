from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.questionnaire_section import QuestionnaireSection
from app.models.questionnaire_template import QuestionnaireTemplate
from app.repositories.base import BaseRepository


class QuestionnaireTemplateRepository(BaseRepository[QuestionnaireTemplate]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=QuestionnaireTemplate)

    def base_query(self) -> Select[tuple[QuestionnaireTemplate]]:
        return (
            select(QuestionnaireTemplate)
            .options(
                selectinload(QuestionnaireTemplate.sections).selectinload(QuestionnaireSection.questions),
            )
        )

    async def list_templates(self, case_type: str | None = None) -> list[QuestionnaireTemplate]:
        query = self.base_query().order_by(
            QuestionnaireTemplate.case_type.asc(),
            desc(QuestionnaireTemplate.version),
        )
        if case_type:
            query = query.where(QuestionnaireTemplate.case_type == case_type)
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def get_full(self, template_id: object) -> QuestionnaireTemplate | None:
        result = await self.session.execute(
            self.base_query().where(QuestionnaireTemplate.id == template_id)
        )
        return result.scalars().unique().one_or_none()

    async def get_active_for_case_type(self, case_type: str) -> QuestionnaireTemplate | None:
        result = await self.session.execute(
            self.base_query()
            .where(
                QuestionnaireTemplate.case_type == case_type,
                QuestionnaireTemplate.status == "active",
            )
            .order_by(desc(QuestionnaireTemplate.version))
        )
        return result.scalars().first()

    async def get_latest_version_for_case_type(self, case_type: str) -> QuestionnaireTemplate | None:
        result = await self.session.execute(
            self.base_query()
            .where(QuestionnaireTemplate.case_type == case_type)
            .order_by(desc(QuestionnaireTemplate.version))
        )
        return result.scalars().first()
