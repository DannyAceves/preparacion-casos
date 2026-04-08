from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.repositories.client import ClientRepository
from app.schemas.client import ClientCreate, ClientUpdate
from app.services.base import BaseService


class ClientService(BaseService[Client, ClientCreate, ClientUpdate]):
    entity_name = "client"

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, repository=ClientRepository(session))
