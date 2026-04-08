from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Client)

    async def find_by_email(self, email: str) -> Client | None:
        result = await self.session.execute(select(Client).where(Client.email == email))
        return result.scalar_one_or_none()
