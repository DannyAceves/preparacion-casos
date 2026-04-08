from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.models.case import Case
from app.services.document_processing_runtime import (
    DOCUMENT_PIPELINE_JOB_TYPES,
    DocumentProcessingRuntimeService,
)


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class FakeSession:
    cases: dict[uuid.UUID, object]
    committed: bool = False

    async def get(self, model: type[object], entity_id: uuid.UUID) -> object | None:
        if model is Case:
            return self.cases.get(entity_id)
        return None

    async def commit(self) -> None:
        self.committed = True


@dataclass
class FakeQueue:
    messages: list[object] = field(default_factory=list)

    async def enqueue(self, message) -> None:
        self.messages.append(message)


@dataclass
class FakeDocumentRepository:
    documents: dict[uuid.UUID, object]

    async def get(self, document_id: uuid.UUID) -> object | None:
        return self.documents.get(document_id)

    async def update(self, entity: object, data: dict) -> object:
        for key, value in data.items():
            setattr(entity, key, value)
        entity.updated_at = _now()
        return entity


@dataclass
class FakeDocumentProcessingJobRepository:
    jobs: list[object] = field(default_factory=list)

    async def get_by_document_job_and_version(self, document_id: uuid.UUID, job_type: str, version_number: int) -> object | None:
        for job in self.jobs:
            if job.document_id == document_id and job.job_type == job_type and job.version_number == version_number:
                return job
        return None

    async def create(self, data: dict) -> object:
        job = SimpleNamespace(id=uuid.uuid4(), created_at=_now(), updated_at=_now(), **data)
        self.jobs.append(job)
        return job

    async def get(self, job_id: uuid.UUID) -> object | None:
        for job in self.jobs:
            if job.id == job_id:
                return job
        return None

    async def update(self, entity: object, data: dict) -> object:
        for key, value in data.items():
            setattr(entity, key, value)
        entity.updated_at = _now()
        return entity

    async def list_for_document(self, document_id: uuid.UUID) -> list[object]:
        return [job for job in self.jobs if job.document_id == document_id]


@dataclass
class FakeAuditLogRepository:
    items: list[dict] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        self.items.append(data)
        return SimpleNamespace(**data)


def build_fixture():
    case_id = uuid.uuid4()
    document_id = uuid.uuid4()
    document = SimpleNamespace(
        id=document_id,
        case_id=case_id,
        version_number=2,
        processing_status="uploaded",
        document_status="uploaded",
        updated_at=_now(),
    )
    session = FakeSession(cases={case_id: SimpleNamespace(id=case_id)})
    queue = FakeQueue()
    service = DocumentProcessingRuntimeService(session, queue)
    service.document_repository = FakeDocumentRepository({document_id: document})
    service.job_repository = FakeDocumentProcessingJobRepository()
    service.audit_log_repository = FakeAuditLogRepository()
    return case_id, document, session, queue, service


@pytest.mark.asyncio
async def test_enqueue_document_pipeline_creates_jobs_and_queue_messages() -> None:
    case_id, document, session, queue, service = build_fixture()

    jobs = await service.enqueue_document_pipeline(
        case_id=case_id,
        document_id=document.id,
        version_number=document.version_number,
        trigger="automatic_upload",
        actor_reference="user-1",
    )

    assert len(jobs) == len(DOCUMENT_PIPELINE_JOB_TYPES)
    assert [job.job_type for job in jobs] == DOCUMENT_PIPELINE_JOB_TYPES
    assert len(queue.messages) == len(DOCUMENT_PIPELINE_JOB_TYPES)
    assert document.processing_status == "queued"
    assert service.audit_log_repository.items[0]["action"] == "document_processing_enqueued"
    assert session.committed is True


@pytest.mark.asyncio
async def test_mark_job_failed_requeues_when_attempts_remaining() -> None:
    case_id, document, session, queue, service = build_fixture()
    job = await service.job_repository.create(
        {
            "case_id": case_id,
            "document_id": document.id,
            "job_type": "ocr_document",
            "status": "running",
            "attempts": 1,
            "max_attempts": 3,
            "version_number": document.version_number,
            "payload": {"trigger": "automatic_upload"},
            "error_message": None,
            "queued_at": _now(),
            "started_at": _now(),
            "finished_at": None,
        }
    )

    updated = await service.mark_job_failed(job.id, "temporary failure")

    assert updated.status == "retrying"
    assert len(queue.messages) == 1
    assert session.committed is True


@pytest.mark.asyncio
async def test_enqueue_document_pipeline_rejects_missing_case() -> None:
    _, document, _, _, service = build_fixture()

    with pytest.raises(HTTPException) as exc_info:
        await service.enqueue_document_pipeline(
            case_id=uuid.uuid4(),
            document_id=document.id,
            version_number=document.version_number,
            trigger="manual",
            actor_reference="user-1",
        )

    assert exc_info.value.status_code == 404
