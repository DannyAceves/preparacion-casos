import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_classification import DocumentClassification
from app.repositories.base import BaseRepository


class DocumentClassificationRepository(BaseRepository[DocumentClassification]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=DocumentClassification)

    async def get_active_for_document(self, document_id: uuid.UUID) -> DocumentClassification | None:
        result = await self.session.execute(
            select(DocumentClassification)
            .where(
                DocumentClassification.document_id == document_id,
                DocumentClassification.is_active.is_(True),
            )
            .order_by(DocumentClassification.created_at.desc())
        )
        return result.scalars().first()

    async def list_for_document(self, document_id: uuid.UUID) -> list[DocumentClassification]:
        result = await self.session.execute(
            select(DocumentClassification)
            .where(DocumentClassification.document_id == document_id)
            .order_by(DocumentClassification.created_at.desc())
        )
        return list(result.scalars().all())

    async def deactivate_active_for_document(self, document_id: uuid.UUID) -> list[DocumentClassification]:
        active_items = await self.list_active_for_document(document_id)
        for item in active_items:
            item.is_active = False
        await self.session.flush()
        return active_items

    async def list_active_for_document(self, document_id: uuid.UUID) -> list[DocumentClassification]:
        result = await self.session.execute(
            select(DocumentClassification)
            .where(
                DocumentClassification.document_id == document_id,
                DocumentClassification.is_active.is_(True),
            )
            .order_by(DocumentClassification.created_at.desc())
        )
        return list(result.scalars().all())
