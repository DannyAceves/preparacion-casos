from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.document import Document
from app.models.document_checklist import CaseDocumentChecklistItem
from app.repositories.document import DocumentRepository
from app.repositories.document_checklist import (
    CaseDocumentChecklistItemRepository,
    DocumentChecklistTemplateRepository,
)
from app.schemas.document_checklist import (
    CaseDocumentChecklistItemCreate,
    CaseDocumentChecklistItemRead,
    CaseDocumentChecklistItemUpdate,
    CaseDocumentChecklistProgress,
    CaseDocumentChecklistRead,
    CaseDocumentChecklistReorderRequest,
)


class DocumentChecklistService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.case_repository = session
        self.template_repository = DocumentChecklistTemplateRepository(session)
        self.item_repository = CaseDocumentChecklistItemRepository(session)
        self.document_repository = DocumentRepository(session)

    async def get_case_checklist(self, case_id: uuid.UUID) -> CaseDocumentChecklistRead:
        case = await self._get_case(case_id)
        items = await self.item_repository.list_for_case(case_id)
        if not items:
            await self._generate_from_template(case)
            await self.session.commit()
            items = await self.item_repository.list_for_case(case_id)

        current_documents = await self.document_repository.list_current_for_case(case_id)
        linked_by_type = self._build_linked_documents_index(current_documents)
        return self._build_checklist_response(case.id, case.case_type, items, linked_by_type)

    async def sync_case_checklist(self, case_id: uuid.UUID) -> CaseDocumentChecklistRead:
        case = await self._get_case(case_id)
        await self._generate_from_template(case, append_missing_only=True)
        await self.session.commit()
        return await self.get_case_checklist(case_id)

    async def add_manual_item(
        self,
        case_id: uuid.UUID,
        payload: CaseDocumentChecklistItemCreate,
    ) -> CaseDocumentChecklistRead:
        case = await self._get_case(case_id)
        existing_items = await self.item_repository.list_for_case(case_id)
        next_order = existing_items[-1].display_order + 1 if existing_items else 0
        await self.item_repository.create(
            {
                "case_id": case.id,
                "template_item_id": None,
                "label": payload.label,
                "document_type": payload.document_type,
                "display_order": next_order,
                "applies": True,
                "requested": False,
                "received": False,
                "validated": False,
                "observations": payload.observations,
                "color_required": payload.color_required,
                "english_translation_required": payload.english_translation_required,
                "signed_copy_required": payload.signed_copy_required,
                "original_required": payload.original_required,
                "copy_only": payload.copy_only,
                "is_manual": True,
            }
        )
        await self.session.commit()
        return await self.get_case_checklist(case_id)

    async def update_item(
        self,
        case_id: uuid.UUID,
        item_id: uuid.UUID,
        payload: CaseDocumentChecklistItemUpdate,
    ) -> CaseDocumentChecklistRead:
        item = await self.item_repository.get_for_case(case_id, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document checklist item not found")

        update_data = payload.model_dump(exclude_unset=True)
        if update_data.get("applies") is False:
            update_data.setdefault("requested", False)
            update_data.setdefault("received", False)
            update_data.setdefault("validated", False)
        if update_data.get("received") is False:
            update_data.setdefault("validated", False)
        await self.item_repository.update(item, update_data)
        await self.session.commit()
        return await self.get_case_checklist(case_id)

    async def reorder_items(
        self,
        case_id: uuid.UUID,
        payload: CaseDocumentChecklistReorderRequest,
    ) -> CaseDocumentChecklistRead:
        items = await self.item_repository.list_for_case(case_id)
        items_by_id = {item.id: item for item in items}
        if set(items_by_id) != set(payload.item_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reorder payload must include all checklist items exactly once",
            )

        for order, item_id in enumerate(payload.item_ids):
            await self.item_repository.update(items_by_id[item_id], {"display_order": order})

        await self.session.commit()
        return await self.get_case_checklist(case_id)

    async def _get_case(self, case_id: uuid.UUID) -> Case:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
        return case

    async def _generate_from_template(self, case: Case, append_missing_only: bool = False) -> None:
        template = await self.template_repository.get_by_case_type(case.case_type)
        if template is None:
            return

        existing_items = await self.item_repository.list_for_case(case.id)
        existing_keys = {
            (item.template_item_id, item.label.strip().lower(), (item.document_type or "").strip().lower())
            for item in existing_items
        }
        next_order = existing_items[-1].display_order + 1 if existing_items else 0

        for template_item in template.items:
            item_key = (
                template_item.id,
                template_item.label.strip().lower(),
                (template_item.document_type or "").strip().lower(),
            )
            if append_missing_only and item_key in existing_keys:
                continue
            await self.item_repository.create(
                {
                    "case_id": case.id,
                    "template_item_id": template_item.id,
                    "label": template_item.label,
                    "document_type": template_item.document_type,
                    "display_order": next_order,
                    "applies": template_item.default_applies,
                    "requested": False,
                    "received": False,
                    "validated": False,
                    "observations": template_item.guidance,
                    "color_required": template_item.color_required,
                    "english_translation_required": template_item.english_translation_required,
                    "signed_copy_required": template_item.signed_copy_required,
                    "original_required": template_item.original_required,
                    "copy_only": template_item.copy_only,
                    "is_manual": False,
                }
            )
            next_order += 1

    def _build_linked_documents_index(self, documents: list[Document]) -> dict[str, list[uuid.UUID]]:
        index: dict[str, list[uuid.UUID]] = {}
        for document in documents:
            for key in {document.document_type, document.classification_label}:
                if not key:
                    continue
                normalized = key.strip().lower()
                index.setdefault(normalized, []).append(document.id)
        return index

    def _build_checklist_response(
        self,
        case_id: uuid.UUID,
        case_type: str | None,
        items: list[CaseDocumentChecklistItem],
        linked_by_type: dict[str, list[uuid.UUID]],
    ) -> CaseDocumentChecklistRead:
        item_reads: list[CaseDocumentChecklistItemRead] = []
        applicable_items = [item for item in items if item.applies]
        requested_items = [item for item in applicable_items if item.requested]
        received_items = [item for item in applicable_items if item.received]
        validated_items = [item for item in applicable_items if item.validated]

        for item in items:
            linked_document_ids: list[uuid.UUID] = []
            if item.document_type:
                linked_document_ids = linked_by_type.get(item.document_type.strip().lower(), [])
            item_reads.append(
                CaseDocumentChecklistItemRead(
                    id=item.id,
                    case_id=item.case_id,
                    template_item_id=item.template_item_id,
                    label=item.label,
                    document_type=item.document_type,
                    display_order=item.display_order,
                    applies=item.applies,
                    requested=item.requested,
                    received=item.received,
                    validated=item.validated,
                    observations=item.observations,
                    color_required=item.color_required,
                    english_translation_required=item.english_translation_required,
                    signed_copy_required=item.signed_copy_required,
                    original_required=item.original_required,
                    copy_only=item.copy_only,
                    is_manual=item.is_manual,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    linked_document_ids=linked_document_ids,
                    linked_document_count=len(linked_document_ids),
                )
            )

        percent_complete = (
            round((len(validated_items) / len(applicable_items)) * 100) if applicable_items else 0
        )
        return CaseDocumentChecklistRead(
            case_id=case_id,
            template_case_type=case_type,
            items=item_reads,
            progress=CaseDocumentChecklistProgress(
                total_items=len(items),
                applicable_items=len(applicable_items),
                requested_items=len(requested_items),
                received_items=len(received_items),
                validated_items=len(validated_items),
                percent_complete=percent_complete,
            ),
        )
