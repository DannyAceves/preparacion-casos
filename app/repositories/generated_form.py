import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_form import GeneratedForm
from app.repositories.base import BaseRepository


class GeneratedFormRepository(BaseRepository[GeneratedForm]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=GeneratedForm)

    async def list_for_case(self, case_id: uuid.UUID) -> list[GeneratedForm]:
        result = await self.session.execute(
            select(GeneratedForm)
            .where(GeneratedForm.case_id == case_id)
            .order_by(GeneratedForm.generated_at.desc(), GeneratedForm.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest_draft_version(self, case_id: uuid.UUID, form_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(GeneratedForm)
            .where(GeneratedForm.case_id == case_id, GeneratedForm.form_id == form_id)
            .order_by(GeneratedForm.draft_version.desc())
        )
        latest = result.scalars().first()
        return latest.draft_version if latest is not None else 0
