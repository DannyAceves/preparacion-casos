from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.case_packet import CasePacket
from app.models.client import Client
from app.models.document import Document
from app.models.inconsistency import Inconsistency
from app.models.participant import Participant
from app.models.review import Review
from app.repositories.audit_log import AuditLogRepository
from app.repositories.case_canonical_field import CaseCanonicalFieldRepository
from app.repositories.case_packet import CasePacketRepository
from app.repositories.document import DocumentRepository
from app.repositories.document_checklist import CaseDocumentChecklistItemRepository
from app.repositories.inconsistency import InconsistencyRepository
from app.repositories.review import ReviewRepository
from app.schemas.case_packet import CasePacketGenerateRequest

DOCUMENT_TYPE_PRIORITY: dict[str, int] = {
    "passport": 10,
    "birth_certificate": 20,
    "marriage_certificate": 30,
    "id": 40,
    "evidence": 90,
    "unclassified": 999,
}

DOCUMENT_SECTION_BY_TYPE: dict[str, str] = {
    "passport": "Identity Documents",
    "birth_certificate": "Civil Documents",
    "marriage_certificate": "Civil Documents",
    "id": "Identity Documents",
    "evidence": "Supporting Evidence",
    "unclassified": "Supporting Evidence",
}

REQUIRED_DOCUMENTS_BY_CASE_TYPE: dict[str, list[tuple[str, str]]] = {
    "family-based": [
        ("passport", "Passport"),
        ("birth_certificate", "Birth Certificate"),
        ("marriage_certificate", "Marriage Certificate"),
        ("evidence", "Supporting Evidence"),
    ],
}


class CasePacketService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.case_packet_repository = CasePacketRepository(session)
        self.document_repository = DocumentRepository(session)
        self.checklist_item_repository = CaseDocumentChecklistItemRepository(session)
        self.canonical_field_repository = CaseCanonicalFieldRepository(session)
        self.inconsistency_repository = InconsistencyRepository(session)
        self.review_repository = ReviewRepository(session)
        self.audit_log_repository = AuditLogRepository(session)

    async def generate_for_case(
        self,
        case_id: uuid.UUID,
        payload: CasePacketGenerateRequest,
    ) -> CasePacket:
        case = await self._get_case(case_id)
        latest_packet = await self.case_packet_repository.get_latest_for_case(case_id)
        current_documents = await self.document_repository.list_current_for_case(case_id)
        valid_documents = self._filter_valid_documents(current_documents)
        sorted_documents = self._sort_documents(valid_documents)
        checklist_items = await self.checklist_item_repository.list_for_case(case_id)
        canonical_fields = await self.canonical_field_repository.list_for_case(case_id)
        inconsistencies = await self.inconsistency_repository.list_for_case(case_id)
        reviews = await self.review_repository.list_for_case(case_id)
        participants = await self._list_participants(case_id)

        packet_version = 1 if latest_packet is None else latest_packet.packet_version + 1
        generated_at = datetime.now(UTC)
        document_index = [self._serialize_document_item(document) for document in sorted_documents]
        summary_payload = self._build_summary_payload(
            case=case,
            participants=participants,
            canonical_fields=canonical_fields,
            inconsistencies=inconsistencies,
            reviews=reviews,
        )
        checklist_payload = self._build_checklist_payload(
            case_type=case.case_type,
            checklist_items=checklist_items,
            documents=sorted_documents,
            inconsistencies=inconsistencies,
        )
        export_artifact = self._build_export_artifact(
            case=case,
            packet_version=packet_version,
            generated_at=generated_at,
            summary_payload=summary_payload,
            document_index=document_index,
            checklist_payload=checklist_payload,
        )
        summary_payload_json = self._to_jsonable(summary_payload)
        document_index_json = self._to_jsonable(document_index)
        checklist_payload_json = self._to_jsonable(checklist_payload)
        export_artifact_json = self._to_jsonable(export_artifact)
        packet = await self.case_packet_repository.create(
            {
                "case_id": case.id,
                "packet_version": packet_version,
                "packet_status": "generated",
                "generated_by_reference": payload.generated_by_reference,
                "summary_payload": summary_payload_json,
                "document_index": document_index_json,
                "checklist_payload": checklist_payload_json,
                "export_artifact": export_artifact_json,
                "generation_notes": payload.generation_notes,
                "generated_at": generated_at,
            }
        )
        await self._create_audit_log(
            case_id=case.id,
            entity_id=packet.id,
            action="case_packet_generated",
            actor_reference=payload.generated_by_reference,
            payload={
                "packet_version": packet.packet_version,
                "document_count": len(document_index),
                "open_inconsistency_count": summary_payload["open_inconsistency_count"],
            },
        )
        await self.session.commit()
        return packet

    async def get_latest_for_case(self, case_id: uuid.UUID) -> CasePacket:
        await self._get_case(case_id)
        packet = await self.case_packet_repository.get_latest_for_case(case_id)
        if packet is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case packet not found")
        return packet

    async def _get_case(self, case_id: uuid.UUID) -> Case:
        result = await self.session.execute(
            select(Case, Client)
            .join(Client, Case.client_id == Client.id)
            .where(Case.id == case_id)
        )
        row = result.first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
        case, client = row
        case.client = client
        return case

    async def _list_participants(self, case_id: uuid.UUID) -> list[Participant]:
        result = await self.session.execute(
            select(Participant)
            .where(Participant.case_id == case_id)
            .order_by(Participant.created_at.asc())
        )
        return list(result.scalars().all())

    def _filter_valid_documents(self, documents: list[Document]) -> list[Document]:
        invalid_statuses = {"rejected", "archived"}
        invalid_processing = {"failed"}
        return [
            document
            for document in documents
            if document.is_current
            and document.document_status not in invalid_statuses
            and document.processing_status not in invalid_processing
        ]

    def _sort_documents(self, documents: list[Document]) -> list[Document]:
        return sorted(
            documents,
            key=lambda document: (
                DOCUMENT_TYPE_PRIORITY.get(document.document_type, 500),
                document.document_type,
                document.original_filename.lower(),
                document.uploaded_at,
            ),
        )

    def _serialize_document_item(self, document: Document) -> dict[str, Any]:
        document_type = document.document_type or "unclassified"
        return {
            "document_id": document.id,
            "document_type": document_type,
            "title": self._humanize_document_type(document_type),
            "original_filename": document.original_filename,
            "classification_label": document.classification_label,
            "classification_confidence_score": document.classification_confidence_score,
            "document_status": document.document_status,
            "processing_status": document.processing_status,
            "priority": DOCUMENT_TYPE_PRIORITY.get(document_type, 500),
            "section": DOCUMENT_SECTION_BY_TYPE.get(document_type, "Supporting Evidence"),
            "uploaded_at": document.uploaded_at,
        }

    def _build_summary_payload(
        self,
        *,
        case: Case,
        participants: list[Participant],
        canonical_fields: list[Any],
        inconsistencies: list[Inconsistency],
        reviews: list[Review],
    ) -> dict[str, Any]:
        open_inconsistencies = [item for item in inconsistencies if item.status in {"open", "under_review"}]
        latest_review = reviews[0] if reviews else None
        return {
            "case_id": case.id,
            "case_number": case.case_number,
            "case_type": case.case_type,
            "case_status": case.status,
            "title": case.title,
            "client": {
                "id": case.client.id,
                "full_name": f"{case.client.first_name} {case.client.last_name}",
                "email": case.client.email,
                "phone": case.client.phone,
            },
            "participants": [
                {
                    "id": participant.id,
                    "role": participant.role,
                    "full_name": f"{participant.first_name} {participant.last_name}",
                    "email": participant.email,
                }
                for participant in participants
            ],
            "canonical_fields": [
                {
                    "field_key": field.field_key,
                    "field_value": field.field_value,
                    "status": field.status,
                    "confidence_score": float(field.confidence_score) if field.confidence_score is not None else None,
                }
                for field in canonical_fields
                if field.status in {"confirmed", "approved"}
            ],
            "open_inconsistency_count": len(open_inconsistencies),
            "latest_review": None
            if latest_review is None
            else {
                "review_type": latest_review.review_type,
                "decision": latest_review.decision,
                "reviewed_at": latest_review.reviewed_at,
                "reviewer_reference": latest_review.reviewer_reference,
            },
        }

    def _build_checklist_payload(
        self,
        *,
        case_type: str,
        checklist_items: list[object],
        documents: list[Document],
        inconsistencies: list[Inconsistency],
    ) -> list[dict[str, Any]]:
        if checklist_items:
            items = [
                {
                    "item_key": f"document:{item.document_type or item.id}",
                    "label": item.label,
                    "status": "ready" if item.validated or item.received else "missing" if item.applies and item.requested else "warning",
                    "required": bool(item.applies and item.requested),
                    "related_document_type": item.document_type,
                    "notes": item.observations,
                }
                for item in checklist_items
                if item.applies
            ]
        else:
            document_types_present = {document.document_type for document in documents}
            required_documents = REQUIRED_DOCUMENTS_BY_CASE_TYPE.get(
                case_type,
                [("passport", "Passport"), ("evidence", "Supporting Evidence")],
            )
            items = [
                {
                    "item_key": f"document:{document_type}",
                    "label": label,
                    "status": "ready" if document_type in document_types_present else "missing",
                    "required": True,
                    "related_document_type": document_type,
                    "notes": None if document_type in document_types_present else f"Missing recommended {label.lower()}.",
                }
                for document_type, label in required_documents
            ]

        open_inconsistencies = [item for item in inconsistencies if item.status in {"open", "under_review"}]
        items.append(
            {
                "item_key": "quality:inconsistencies",
                "label": "Open inconsistencies review",
                "status": "ready" if not open_inconsistencies else "warning",
                "required": True,
                "related_document_type": None,
                "notes": None if not open_inconsistencies else f"{len(open_inconsistencies)} open inconsistencies require attention.",
            }
        )
        return items

    def _build_export_artifact(
        self,
        *,
        case: Case,
        packet_version: int,
        generated_at: datetime,
        summary_payload: dict[str, Any],
        document_index: list[dict[str, Any]],
        checklist_payload: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "artifact_type": "case_review_packet",
            "format": "json",
            "generated_at": generated_at,
            "packet_version": packet_version,
            "sections": [
                {"key": "summary", "title": "Case Summary", "content": summary_payload},
                {"key": "index", "title": "Document Index", "content": document_index},
                {"key": "checklist", "title": "Checklist", "content": checklist_payload},
            ],
            "prefilled_forms_placeholder": {
                "ready": False,
                "case_type": case.case_type,
                "available_templates": [],
                "notes": "Reserved for future prefilled form generation.",
            },
        }

    def _humanize_document_type(self, document_type: str) -> str:
        return document_type.replace("_", " ").title()

    def _to_jsonable(self, value: Any) -> Any:
        return jsonable_encoder(value)

    async def _create_audit_log(
        self,
        *,
        case_id: uuid.UUID,
        entity_id: uuid.UUID,
        action: str,
        actor_reference: str | None,
        payload: dict[str, Any],
    ) -> AuditLog:
        return await self.audit_log_repository.create(
            {
                "case_id": case_id,
                "entity_type": "case_packet",
                "entity_id": str(entity_id),
                "action": action,
                "actor_reference": actor_reference,
                "payload": payload,
                "occurred_at": datetime.now(UTC),
            }
        )
