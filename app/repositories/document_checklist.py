import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document_checklist import (
    CaseDocumentChecklistItem,
    DocumentChecklistTemplate,
)
from app.repositories.base import BaseRepository


class DocumentChecklistTemplateRepository(BaseRepository[DocumentChecklistTemplate]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=DocumentChecklistTemplate)

    async def get_by_case_type(self, case_type: str) -> DocumentChecklistTemplate | None:
        result = await self.session.execute(
            select(DocumentChecklistTemplate)
            .options(selectinload(DocumentChecklistTemplate.items))
            .where(DocumentChecklistTemplate.case_type == case_type)
        )
        return result.scalar_one_or_none()


class CaseDocumentChecklistItemRepository(BaseRepository[CaseDocumentChecklistItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=CaseDocumentChecklistItem)

    async def list_for_case(self, case_id: uuid.UUID) -> list[CaseDocumentChecklistItem]:
        result = await self.session.execute(
            select(CaseDocumentChecklistItem)
            .where(CaseDocumentChecklistItem.case_id == case_id)
            .order_by(CaseDocumentChecklistItem.display_order.asc(), CaseDocumentChecklistItem.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_for_case(self, case_id: uuid.UUID, item_id: uuid.UUID) -> CaseDocumentChecklistItem | None:
        result = await self.session.execute(
            select(CaseDocumentChecklistItem).where(
                CaseDocumentChecklistItem.case_id == case_id,
                CaseDocumentChecklistItem.id == item_id,
            )
        )
        return result.scalar_one_or_none()
