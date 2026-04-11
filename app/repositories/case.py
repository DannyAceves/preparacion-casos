from sqlalchemy import Select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.repositories.base import BaseRepository


class CaseRepository(BaseRepository[Case]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Case)

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Case]:
        sortable_columns = {
            "created_at": Case.created_at,
            "updated_at": Case.updated_at,
            "case_number": Case.case_number,
            "title": Case.title,
            "status": Case.status,
            "case_type": Case.case_type,
        }
        order_column = sortable_columns.get(sort_by, Case.created_at)
        order_clause = desc(order_column) if sort_order.lower() != "asc" else order_column.asc()

        query: Select[tuple[Case]] = self.base_query().order_by(order_clause)
        if offset > 0:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())
