import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_processing_job import DocumentProcessingJob
from app.repositories.base import BaseRepository


class DocumentProcessingJobRepository(BaseRepository[DocumentProcessingJob]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=DocumentProcessingJob)

    async def list_for_document(self, document_id: uuid.UUID) -> list[DocumentProcessingJob]:
        result = await self.session.execute(
            select(DocumentProcessingJob)
            .where(DocumentProcessingJob.document_id == document_id)
            .order_by(DocumentProcessingJob.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_document_job_and_version(
        self,
        document_id: uuid.UUID,
        job_type: str,
        version_number: int,
    ) -> DocumentProcessingJob | None:
        result = await self.session.execute(
            select(DocumentProcessingJob).where(
                DocumentProcessingJob.document_id == document_id,
                DocumentProcessingJob.job_type == job_type,
                DocumentProcessingJob.version_number == version_number,
            )
        )
        return result.scalars().first()
