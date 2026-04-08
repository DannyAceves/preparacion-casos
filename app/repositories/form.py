from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.form import Form
from app.repositories.base import BaseRepository


class FormRepository(BaseRepository[Form]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Form)

    async def list_active_for_case_type(self, case_type_id: str) -> list[Form]:
        result = await self.session.execute(
            select(Form)
            .where(Form.case_type_id == case_type_id, Form.is_active.is_(True))
            .order_by(Form.form_code.asc(), Form.version.desc())
        )
        return list(result.scalars().all())
