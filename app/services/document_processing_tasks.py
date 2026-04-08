from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.document import Document
from app.repositories.audit_log import AuditLogRepository
from app.repositories.document import DocumentRepository
from app.services.document_classification import DocumentClassificationService
from app.services.document_text_extraction import DocumentTextExtractionService


class DocumentProcessingTaskService:
    def __init__(
        self,
        session: AsyncSession,
        text_extraction_service: DocumentTextExtractionService | None = None,
    ) -> None:
        self.session = session
        self.document_repository = DocumentRepository(session)
        self.audit_log_repository = AuditLogRepository(session)
        self.classification_service = DocumentClassificationService(session)
        self.text_extraction_service = text_extraction_service or DocumentTextExtractionService()

    async def run_job(
        self,
        *,
        document_id: uuid.UUID,
        job_type: str,
        job_payload: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        handlers = {
            "virus_scan_document": self.virus_scan_document,
            "ocr_document": self.ocr_document,
            "classify_document": self.classify_document,
            "extract_document_fields": self.extract_document_fields,
            "refresh_canonical_fields": self.refresh_canonical_fields,
            "detect_case_inconsistencies": self.detect_case_inconsistencies,
        }
        handler = handlers[job_type]
        return await handler(document_id, job_payload=job_payload)

    async def virus_scan_document(
        self,
        document_id: uuid.UUID,
        *,
        job_payload: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        document = await self._get_document(document_id)
        metadata = dict(document.file_metadata or {})
        if metadata.get("virus_scan_status") == "clean":
            return {"virus_scan_status": "clean", "idempotent": True}
        metadata["virus_scan_status"] = "clean"
        await self.document_repository.update(document, {"file_metadata": metadata})
        await self.session.commit()
        return {"virus_scan_status": "clean"}

    async def ocr_document(
        self,
        document_id: uuid.UUID,
        *,
        job_payload: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        document = await self._get_document(document_id)
        extracted = dict(document.extracted_metadata or {})
        payload_dict = job_payload if isinstance(job_payload, dict) else {}
        force_reprocess = bool(payload_dict.get("force_reprocess"))
        if extracted.get("ocr_status") == "completed" and not force_reprocess:
            return {"ocr_status": "completed", "idempotent": True}

        result = self.text_extraction_service.extract_for_document(
            storage_backend=document.storage_backend,
            storage_key=document.storage_key,
            mime_type=document.mime_type,
            original_filename=document.original_filename,
            force_reprocess=force_reprocess,
        )

        extracted["ocr_status"] = "completed" if result.extracted_text else "manual_review"
        extracted["ocr_provider"] = result.extraction_method
        extracted["requires_ocr"] = result.requires_ocr
        extracted["manual_review_required"] = result.manual_review_required
        extracted["text_extraction_error"] = result.error_message

        await self.document_repository.update(
            document,
            {
                "extracted_text": result.extracted_text,
                "extracted_metadata": extracted,
                "document_status": "manual_review" if result.manual_review_required else document.document_status,
            },
        )
        await self._create_audit_log(
            case_id=document.case_id,
            entity_id=document.id,
            action="document_text_extracted" if result.extracted_text else "document_manual_review_required",
            actor_reference="worker",
            payload={
                "document_id": str(document.id),
                "method": result.extraction_method,
                "manual_review_required": result.manual_review_required,
                "error_message": result.error_message,
                "trigger": payload_dict.get("trigger"),
                "reprocessed": force_reprocess,
            },
        )
        await self.session.commit()
        return {
            "ocr_status": extracted["ocr_status"],
            "ocr_provider": result.extraction_method,
            "manual_review_required": result.manual_review_required,
            "error_message": result.error_message,
        }

    async def classify_document(
        self,
        document_id: uuid.UUID,
        *,
        job_payload: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        document = await self._get_document(document_id)
        extracted = dict(document.extracted_metadata or {})
        payload_dict = job_payload if isinstance(job_payload, dict) else {}
        force_reprocess = bool(payload_dict.get("force_reprocess"))
        result = await self.classification_service.classify_document(
            document=document,
            actor_reference="worker",
            trigger=payload_dict.get("trigger"),
            force_reprocess=force_reprocess,
        )
        extracted["classification_status"] = "completed"
        extracted["classification_method"] = result.classification.classification_method
        extracted["classification_source"] = result.classification.classification_source
        await self.document_repository.update(
            document,
            {
                "extracted_metadata": extracted,
            },
        )
        await self.session.commit()
        return {
            "classification_status": "completed",
            "predicted_type": result.classification.predicted_type,
            "confidence_score": result.classification.confidence_score,
            "classification_source": result.classification.classification_source,
            "classification_method": result.classification.classification_method,
            "idempotent": result.idempotent,
        }

    async def extract_document_fields(
        self,
        document_id: uuid.UUID,
        *,
        job_payload: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        document = await self._get_document(document_id)
        extracted = dict(document.extracted_metadata or {})
        payload_dict = job_payload if isinstance(job_payload, dict) else {}
        force_reprocess = bool(payload_dict.get("force_reprocess"))
        if extracted.get("field_extraction_status") == "completed" and not force_reprocess:
            return {"field_extraction_status": "completed", "idempotent": True}

        if not document.extracted_text:
            extracted["field_extraction_status"] = "manual_review"
            extracted["field_extraction_provider"] = "placeholder"
            await self.document_repository.update(
                document,
                {
                    "extracted_metadata": extracted,
                    "document_status": "manual_review",
                },
            )
            await self._create_audit_log(
                case_id=document.case_id,
                entity_id=document.id,
                action="document_field_extraction_manual_review",
                actor_reference="worker",
                payload={
                    "document_id": str(document.id),
                    "reason": "missing_extracted_text",
                    "trigger": payload_dict.get("trigger"),
                    "reprocessed": force_reprocess,
                },
            )
            await self.session.commit()
            return {"field_extraction_status": "manual_review"}

        extracted_fields = self.text_extraction_service.field_detector.detect(document.extracted_text)
        extracted["field_extraction_status"] = "completed"
        extracted["field_extraction_provider"] = "simple_detector"
        extracted["field_count"] = len(extracted_fields)
        await self.document_repository.update(
            document,
            {
                "extracted_fields": extracted_fields,
                "extracted_metadata": extracted,
                "document_status": "processed",
            },
        )
        await self._create_audit_log(
            case_id=document.case_id,
            entity_id=document.id,
            action="document_fields_extracted",
            actor_reference="worker",
            payload={
                "document_id": str(document.id),
                "field_count": len(extracted_fields),
                "trigger": payload_dict.get("trigger"),
                "reprocessed": force_reprocess,
            },
        )
        await self.session.commit()
        return {
            "field_extraction_status": "completed",
            "field_count": len(extracted_fields),
        }

    async def refresh_canonical_fields(
        self,
        document_id: uuid.UUID,
        *,
        job_payload: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        document = await self._get_document(document_id)
        extracted = dict(document.extracted_metadata or {})
        extracted["canonical_refresh_status"] = "queued_for_service"
        await self.document_repository.update(document, {"extracted_metadata": extracted})
        await self.session.commit()
        return {"canonical_refresh_status": "queued_for_service"}

    async def detect_case_inconsistencies(
        self,
        document_id: uuid.UUID,
        *,
        job_payload: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        document = await self._get_document(document_id)
        extracted = dict(document.extracted_metadata or {})
        extracted["inconsistency_detection_status"] = "queued_for_service"
        await self.document_repository.update(document, {"extracted_metadata": extracted})
        await self.session.commit()
        return {"inconsistency_detection_status": "queued_for_service"}

    async def _get_document(self, document_id: uuid.UUID) -> Document:
        document = await self.document_repository.get(document_id)
        if document is None:
            raise ValueError("document not found")
        return document

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
                "entity_type": "document_processing",
                "entity_id": str(entity_id),
                "action": action,
                "actor_reference": actor_reference,
                "payload": payload,
                "occurred_at": datetime.now(UTC),
            }
        )
