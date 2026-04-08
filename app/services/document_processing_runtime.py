from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.document import Document
from app.models.document_processing_job import DocumentProcessingJob
from app.queue.redis_queue import RedisQueue
from app.repositories.audit_log import AuditLogRepository
from app.repositories.document import DocumentRepository
from app.repositories.document_processing_job import DocumentProcessingJobRepository
from app.schemas.document_processing import DocumentProcessingJobCreate, QueueJobMessage

DOCUMENT_PIPELINE_JOB_TYPES = [
    "virus_scan_document",
    "ocr_document",
    "classify_document",
    "extract_document_fields",
    "refresh_canonical_fields",
    "detect_case_inconsistencies",
]


class DocumentProcessingRuntimeService:
    def __init__(self, session: AsyncSession, queue: RedisQueue) -> None:
        self.session = session
        self.queue = queue
        self.document_repository = DocumentRepository(session)
        self.job_repository = DocumentProcessingJobRepository(session)
        self.audit_log_repository = AuditLogRepository(session)

    async def enqueue_document_pipeline(
        self,
        *,
        case_id: uuid.UUID,
        document_id: uuid.UUID,
        version_number: int,
        trigger: str,
        actor_reference: str | None,
    ) -> list[DocumentProcessingJob]:
        await self._get_case(case_id)
        document = await self._get_document(document_id)
        jobs: list[DocumentProcessingJob] = []

        for job_type in DOCUMENT_PIPELINE_JOB_TYPES:
            existing = await self.job_repository.get_by_document_job_and_version(document.id, job_type, version_number)
            if existing is not None:
                if trigger == "manual_reprocess":
                    existing = await self.job_repository.update(
                        existing,
                        {
                            "status": "queued",
                            "error_message": None,
                            "started_at": None,
                            "finished_at": None,
                            "payload": {
                                "trigger": trigger,
                                "force_reprocess": True,
                            },
                        },
                    )
                jobs.append(existing)
                continue

            job = await self.job_repository.create(
                DocumentProcessingJobCreate(
                    case_id=case_id,
                    document_id=document.id,
                    job_type=job_type,
                    status="queued",
                    attempts=0,
                    max_attempts=settings.document_processing_max_attempts,
                    version_number=version_number,
                    payload={
                        "trigger": trigger,
                        "force_reprocess": trigger == "manual_reprocess",
                    },
                    queued_at=datetime.now(UTC),
                ).model_dump()
            )
            jobs.append(job)

        await self.document_repository.update(
            document,
            {
                "processing_status": "queued",
                "document_status": document.document_status,
            },
        )
        await self._create_audit_log(
            case_id=case_id,
            entity_id=document.id,
            action="document_reprocessing_enqueued" if trigger == "manual_reprocess" else "document_processing_enqueued",
            actor_reference=actor_reference,
            payload={
                "document_id": str(document.id),
                "version_number": version_number,
                "trigger": trigger,
                "jobs": [job.job_type for job in jobs],
            },
        )
        await self.session.commit()

        for job in jobs:
            if job.status in {"queued", "retrying"}:
                await self.queue.enqueue(
                    QueueJobMessage(
                        job_id=job.id,
                        case_id=job.case_id,
                        document_id=job.document_id,
                        job_type=job.job_type,
                        version_number=job.version_number,
                        trigger=trigger,
                    )
                )
        return jobs

    async def mark_job_running(self, job_id: uuid.UUID) -> DocumentProcessingJob:
        job = await self._get_job(job_id)
        if job.status == "completed":
            return job
        updated = await self.job_repository.update(
            job,
            {
                "status": "running",
                "attempts": job.attempts + 1,
                "started_at": datetime.now(UTC),
                "error_message": None,
            },
        )
        document = await self._get_document(updated.document_id)
        await self.document_repository.update(document, {"processing_status": "processing"})
        await self.session.commit()
        return updated

    async def mark_job_completed(self, job_id: uuid.UUID, payload: dict[str, Any] | None = None) -> DocumentProcessingJob:
        job = await self._get_job(job_id)
        updated = await self.job_repository.update(
            job,
            {
                "status": "completed",
                "finished_at": datetime.now(UTC),
                "payload": payload or job.payload,
                "error_message": None,
            },
        )
        await self._refresh_document_processing_status(updated.document_id)
        await self.session.commit()
        return updated

    async def mark_job_failed(self, job_id: uuid.UUID, error_message: str) -> DocumentProcessingJob:
        job = await self._get_job(job_id)
        should_retry = job.attempts < job.max_attempts
        updated = await self.job_repository.update(
            job,
            {
                "status": "retrying" if should_retry else "failed",
                "finished_at": datetime.now(UTC),
                "error_message": error_message,
            },
        )
        if should_retry:
            await self.queue.enqueue(
                QueueJobMessage(
                    job_id=updated.id,
                    case_id=updated.case_id,
                    document_id=updated.document_id,
                    job_type=updated.job_type,
                    version_number=updated.version_number,
                    trigger="retry",
                )
            )
        await self._refresh_document_processing_status(updated.document_id)
        await self.session.commit()
        return updated

    async def _refresh_document_processing_status(self, document_id: uuid.UUID) -> None:
        jobs = await self.job_repository.list_for_document(document_id)
        document = await self._get_document(document_id)
        statuses = {job.status for job in jobs}
        if statuses and statuses <= {"completed"}:
            await self.document_repository.update(document, {"processing_status": "processed"})
            return
        if "failed" in statuses:
            await self.document_repository.update(document, {"processing_status": "failed"})
            return
        if "running" in statuses or "retrying" in statuses:
            await self.document_repository.update(document, {"processing_status": "processing"})
            return
        await self.document_repository.update(document, {"processing_status": "queued"})

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

    async def _get_job(self, job_id: uuid.UUID) -> DocumentProcessingJob:
        job = await self.job_repository.get(job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document processing job not found")
        return job

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
