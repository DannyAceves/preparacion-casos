import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Document)

    async def list_current_for_case(self, case_id: uuid.UUID) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where(Document.case_id == case_id, Document.is_current.is_(True))
            .order_by(Document.uploaded_at.desc(), Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_with_lineage(self, document_id: uuid.UUID) -> Document | None:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalars().first()

    async def list_versions(self, root_document_id: uuid.UUID) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where(Document.root_document_id == root_document_id)
            .order_by(Document.version_number.asc())
        )
        return list(result.scalars().all())

    async def get_current_by_root(self, root_document_id: uuid.UUID) -> Document | None:
        result = await self.session.execute(
            select(Document).where(
                Document.root_document_id == root_document_id,
                Document.is_current.is_(True),
            )
        )
        return result.scalars().first()
