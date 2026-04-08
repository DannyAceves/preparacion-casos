from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.document import Document
from app.repositories.audit_log import AuditLogRepository
from app.repositories.document import DocumentRepository
from app.schemas.document import DocumentClassificationUpdate, DocumentCreate, DocumentDetailRead, DocumentRead, DocumentVersionSummaryRead
from app.queue.redis_queue import RedisQueue
from app.storage.base import DocumentStorage
from app.storage.factory import get_document_storage
from app.queue.redis_client import get_redis_client
from app.services.document_classification import DocumentClassificationService
from app.services.document_processing_runtime import DocumentProcessingRuntimeService

logger = logging.getLogger(__name__)


class DocumentManagementService:
    def __init__(
        self,
        session: AsyncSession,
        storage: DocumentStorage | None = None,
        processing_queue: RedisQueue | None = None,
    ) -> None:
        self.session = session
        self.storage = storage or get_document_storage()
        self.processing_queue = processing_queue or RedisQueue(get_redis_client())
        self.document_repository = DocumentRepository(session)
        self.audit_log_repository = AuditLogRepository(session)
        self.classification_service = DocumentClassificationService(session)

    async def upload_document(
        self,
        *,
        case_id: uuid.UUID,
        uploaded_by_user_id: str,
        file: UploadFile,
        document_status: str = "uploaded",
        classification_label: str | None = None,
        classification_source: str | None = None,
    ) -> Document:
        case = await self._get_case(case_id)
        contents = await self._read_and_validate_file(file)
        stored_file = await self.storage.save(
            case_reference=str(case.id),
            original_filename=file.filename or "upload.bin",
            content=contents,
        )

        sha256_hash = hashlib.sha256(contents).hexdigest()
        metadata = self._build_file_metadata(contents)
        effective_classification = classification_label or "unclassified"

        document = await self.document_repository.create(
            DocumentCreate(
                case_id=case.id,
                uploaded_by_user_id=uploaded_by_user_id,
                document_type=effective_classification,
                original_filename=file.filename or stored_file.stored_filename,
                stored_filename=stored_file.stored_filename,
                storage_backend=stored_file.storage_backend,
                storage_key=stored_file.storage_key,
                mime_type=file.content_type or "application/octet-stream",
                size_bytes=len(contents),
                sha256_hash=sha256_hash,
                document_status=document_status,
                processing_status=document_status,
                classification_label=classification_label,
                classification_source=classification_source,
                classification_confidence_score=1.0 if classification_label else None,
                file_metadata=metadata,
                extracted_metadata=None,
                version_number=1,
                is_current=True,
                previous_version_id=None,
                root_document_id=None,
                replacement_notes=None,
                uploaded_at=datetime.now(UTC),
            ).model_dump()
        )
        document = await self.document_repository.update(
            document,
            {"root_document_id": document.id},
        )
        if classification_label is not None and classification_source is not None:
            await self.classification_service.review_document_classification(
                document=document,
                payload=DocumentClassificationUpdate(
                    classification_label=classification_label,
                    classification_source=classification_source,
                    classification_confidence_score=1.0,
                    reviewed_by_user_id=uploaded_by_user_id,
                    review_notes="Initial classification provided on upload.",
                ),
            )
        await self._create_audit_log(
            case_id=case.id,
            entity_id=document.id,
            action="document_uploaded",
            actor_reference=uploaded_by_user_id,
            payload={
                "case_id": str(case.id),
                "version_number": document.version_number,
                "document_status": document.document_status,
            },
        )
        await self.session.commit()
        await self._enqueue_document_processing_if_enabled(
            case_id=case.id,
            document=document,
            actor_reference=uploaded_by_user_id,
            trigger="automatic_upload",
        )
        return document

    async def list_case_documents(self, case_id: uuid.UUID) -> list[Document]:
        await self._get_case(case_id)
        return await self.document_repository.list_current_for_case(case_id)

    async def get_document_detail(self, document_id: uuid.UUID) -> DocumentDetailRead:
        document = await self._get_document(document_id)
        root_document_id = document.root_document_id or document.id
        versions = await self.document_repository.list_versions(root_document_id)
        return DocumentDetailRead(
            **DocumentRead.model_validate(document).model_dump(),
            versions=[DocumentVersionSummaryRead.model_validate(version) for version in versions],
        )

    async def replace_document(
        self,
        *,
        document_id: uuid.UUID,
        uploaded_by_user_id: str,
        file: UploadFile,
        document_status: str | None = None,
        replacement_notes: str | None = None,
    ) -> Document:
        current_document = await self._get_document(document_id)
        contents = await self._read_and_validate_file(file)
        stored_file = await self.storage.save(
            case_reference=str(current_document.case_id),
            original_filename=file.filename or current_document.original_filename,
            content=contents,
        )
        sha256_hash = hashlib.sha256(contents).hexdigest()
        metadata = self._build_file_metadata(contents)

        await self.document_repository.update(current_document, {"is_current": False})
        new_document = await self.document_repository.create(
            DocumentCreate(
                case_id=current_document.case_id,
                uploaded_by_user_id=uploaded_by_user_id,
                document_type=current_document.document_type,
                original_filename=file.filename or current_document.original_filename,
                stored_filename=stored_file.stored_filename,
                storage_backend=stored_file.storage_backend,
                storage_key=stored_file.storage_key,
                mime_type=file.content_type or current_document.mime_type,
                size_bytes=len(contents),
                sha256_hash=sha256_hash,
                document_status=document_status or current_document.document_status,
                processing_status=document_status or current_document.document_status,
                classification_label=current_document.classification_label,
                classification_source=current_document.classification_source,
                classification_confidence_score=current_document.classification_confidence_score,
                file_metadata=metadata,
                extracted_metadata=current_document.extracted_metadata,
                version_number=current_document.version_number + 1,
                is_current=True,
                previous_version_id=current_document.id,
                root_document_id=current_document.root_document_id or current_document.id,
                replacement_notes=replacement_notes,
                uploaded_at=datetime.now(UTC),
            ).model_dump()
        )
        await self._create_audit_log(
            case_id=current_document.case_id,
            entity_id=new_document.id,
            action="document_replaced",
            actor_reference=uploaded_by_user_id,
            payload={
                "case_id": str(new_document.case_id),
                "previous_version_id": str(current_document.id),
                "root_document_id": str(new_document.root_document_id),
                "version_number": new_document.version_number,
            },
        )
        await self.session.commit()
        await self._enqueue_document_processing_if_enabled(
            case_id=current_document.case_id,
            document=new_document,
            actor_reference=uploaded_by_user_id,
            trigger="automatic_replace",
        )
        return new_document

    async def update_classification(
        self,
        document_id: uuid.UUID,
        payload: DocumentClassificationUpdate,
    ) -> Document:
        document = await self._get_document(document_id)
        await self.classification_service.review_document_classification(
            document=document,
            payload=payload,
        )
        updated = await self._get_document(document_id)
        await self.session.commit()
        return updated

    async def enqueue_reprocessing(
        self,
        *,
        document_id: uuid.UUID,
        actor_reference: str,
    ) -> None:
        document = await self._get_document(document_id)
        runtime = DocumentProcessingRuntimeService(self.session, self.processing_queue)
        await runtime.enqueue_document_pipeline(
            case_id=document.case_id,
            document_id=document.id,
            version_number=document.version_number,
            trigger="manual_reprocess",
            actor_reference=actor_reference,
        )

    async def _get_case(self, case_id: uuid.UUID) -> Case:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
        return case

    async def _get_document(self, document_id: uuid.UUID) -> Document:
        document = await self.document_repository.get(document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document not found")
        return document

    async def _read_and_validate_file(self, file: UploadFile) -> bytes:
        contents = await file.read()
        mime_type = file.content_type or "application/octet-stream"
        if mime_type not in settings.document_allowed_mime_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file type is not allowed",
            )
        if len(contents) > settings.document_max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file exceeds maximum allowed size",
            )
        return contents

    def _build_file_metadata(self, contents: bytes) -> dict[str, int]:
        return {"size_bytes": len(contents)}

    async def _create_audit_log(
        self,
        *,
        case_id: uuid.UUID,
        entity_id: uuid.UUID,
        action: str,
        actor_reference: str,
        payload: dict,
    ) -> AuditLog:
        return await self.audit_log_repository.create(
            {
                "case_id": case_id,
                "entity_type": "document",
                "entity_id": str(entity_id),
                "action": action,
                "actor_reference": actor_reference,
                "payload": payload,
                "occurred_at": datetime.now(UTC),
            }
        )

    async def _enqueue_document_processing_if_enabled(
        self,
        *,
        case_id: uuid.UUID,
        document: Document,
        actor_reference: str,
        trigger: str,
    ) -> None:
        if not settings.document_processing_auto_enqueue:
            return
        runtime = DocumentProcessingRuntimeService(self.session, self.processing_queue)
        try:
            await runtime.enqueue_document_pipeline(
                case_id=case_id,
                document_id=document.id,
                version_number=document.version_number,
                trigger=trigger,
                actor_reference=actor_reference,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Document processing enqueue failed", exc_info=exc)
