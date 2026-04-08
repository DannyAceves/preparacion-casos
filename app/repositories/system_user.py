from sqlalchemy import String, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.core.auth import SystemRole
from app.models.system_user import SystemUser
from app.repositories.base import BaseRepository


class SystemUserRepository(BaseRepository[SystemUser]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=SystemUser)

    async def find_by_email(self, email: str) -> SystemUser | None:
        normalized = email.strip().lower()
        result = await self.session.execute(
            select(SystemUser).where(func.lower(SystemUser.email) == normalized)
        )
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        *,
        search: str | None = None,
        role: SystemRole | None = None,
        is_active: bool | None = None,
    ) -> list[SystemUser]:
        query: Select[tuple[SystemUser]] = self.base_query()

        if search:
            normalized = f"%{search.strip()}%"
            full_name = (SystemUser.first_name + " " + SystemUser.last_name).cast(String)
            query = query.where(
                or_(
                    SystemUser.first_name.ilike(normalized),
                    SystemUser.last_name.ilike(normalized),
                    SystemUser.email.ilike(normalized),
                    full_name.ilike(normalized),
                )
            )

        if role is not None:
            query = query.where(SystemUser.role == role)

        if is_active is not None:
            query = query.where(SystemUser.is_active == is_active)

        result = await self.session.execute(query.order_by(SystemUser.last_name.asc(), SystemUser.first_name.asc()))
        return list(result.scalars().all())
