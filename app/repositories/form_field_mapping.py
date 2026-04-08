import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.form_field_mapping import FormFieldMapping
from app.repositories.base import BaseRepository


class FormFieldMappingRepository(BaseRepository[FormFieldMapping]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=FormFieldMapping)

    async def list_for_form(self, form_id: uuid.UUID) -> list[FormFieldMapping]:
        result = await self.session.execute(
            select(FormFieldMapping)
            .where(FormFieldMapping.form_id == form_id)
            .order_by(FormFieldMapping.form_field_key.asc())
        )
        return list(result.scalars().all())
