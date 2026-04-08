from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.document import Document
from app.repositories.document import DocumentRepository
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.services.base import BaseService


class DocumentService(BaseService[Document, DocumentCreate, DocumentUpdate]):
    entity_name = "document"

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, repository=DocumentRepository(session))

    async def create(self, payload: DocumentCreate) -> Document:
        await self.ensure_exists(Case, payload.case_id, "case")
        return await super().create(payload)

    async def update(self, entity_id: uuid.UUID, payload: DocumentUpdate) -> Document:
        if payload.case_id is not None:
            await self.ensure_exists(Case, payload.case_id, "case")
        return await super().update(entity_id, payload)
