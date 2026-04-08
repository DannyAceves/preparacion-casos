from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.models.case import Case
from app.services.document_management import DocumentManagementService
from app.schemas.document import DocumentClassificationUpdate


def _now() -> datetime:
    return datetime.now(UTC)


class FakeUploadFile:
    def __init__(self, filename: str, content_type: str, content: bytes) -> None:
        self.filename = filename
        self.content_type = content_type
        self._content = content

    async def read(self) -> bytes:
        return self._content


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
class FakeStoredFile:
    stored_filename: str
    storage_key: str
    storage_backend: str
    absolute_path: Path


@dataclass
class FakeStorage:
    saves: list[dict] = field(default_factory=list)

    async def save(self, *, case_reference: str, original_filename: str, content: bytes) -> FakeStoredFile:
        self.saves.append(
            {
                "case_reference": case_reference,
                "original_filename": original_filename,
                "size_bytes": len(content),
            }
        )
        return FakeStoredFile(
            stored_filename=f"stored-{original_filename}",
            storage_key=f"{case_reference}/stored-{original_filename}",
            storage_backend="local",
            absolute_path=Path("/tmp") / f"stored-{original_filename}",
        )


@dataclass
class FakeDocumentRepository:
    documents: list[object] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        document = SimpleNamespace(
            id=uuid.uuid4(),
            created_at=_now(),
            updated_at=_now(),
            **data,
        )
        self.documents.append(document)
        return document

    async def update(self, entity: object, data: dict) -> object:
        for key, value in data.items():
            setattr(entity, key, value)
        entity.updated_at = _now()
        return entity

    async def get(self, document_id: uuid.UUID) -> object | None:
        for document in self.documents:
            if document.id == document_id:
                return document
        return None

    async def list_current_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [
            document
            for document in self.documents
            if document.case_id == case_id and document.is_current
        ]

    async def list_versions(self, root_document_id: uuid.UUID) -> list[object]:
        return sorted(
            [
                document
                for document in self.documents
                if (document.root_document_id or document.id) == root_document_id
            ],
            key=lambda item: item.version_number,
        )


@dataclass
class FakeAuditLogRepository:
    entries: list[dict] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        self.entries.append(data)
        return SimpleNamespace(**data)


@dataclass
class FakeClassificationService:
    entries: list[dict] = field(default_factory=list)

    async def review_document_classification(self, *, document: object, payload: DocumentClassificationUpdate) -> object:
        document.classification_label = payload.classification_label
        document.classification_source = payload.classification_source
        document.classification_confidence_score = payload.classification_confidence_score if payload.classification_confidence_score is not None else 1.0
        document.document_type = payload.classification_label
        entry = {
            "document_id": document.id,
            "predicted_type": payload.classification_label,
            "classification_source": payload.classification_source,
            "confidence_score": document.classification_confidence_score,
            "reviewed_by_user_id": payload.reviewed_by_user_id,
            "review_notes": payload.review_notes,
        }
        self.entries.append(entry)
        return SimpleNamespace(**entry)


def build_service_fixture() -> tuple[
    uuid.UUID,
    FakeSession,
    FakeStorage,
    FakeDocumentRepository,
    FakeAuditLogRepository,
    DocumentManagementService,
]:
    case_id = uuid.uuid4()
    session = FakeSession(cases={case_id: SimpleNamespace(id=case_id, case_type="family-based")})
    storage = FakeStorage()
    document_repository = FakeDocumentRepository()
    audit_repository = FakeAuditLogRepository()
    classification_service = FakeClassificationService()
    service = DocumentManagementService(session, storage=storage)
    service.document_repository = document_repository
    service.audit_log_repository = audit_repository
    service.classification_service = classification_service
    return case_id, session, storage, document_repository, audit_repository, service


@pytest.mark.asyncio
async def test_upload_document_creates_initial_version_and_audit() -> None:
    case_id, session, storage, document_repository, audit_repository, service = build_service_fixture()
    file_bytes = b"sample-pdf"

    document = await service.upload_document(
        case_id=case_id,
        uploaded_by_user_id="user-1",
        file=FakeUploadFile("evidence.pdf", "application/pdf", file_bytes),
        classification_label="evidence",
        classification_source="manual",
    )

    assert document.case_id == case_id
    assert document.version_number == 1
    assert document.root_document_id == document.id
    assert document.is_current is True
    assert document.sha256_hash == hashlib.sha256(file_bytes).hexdigest()
    assert storage.saves[0]["original_filename"] == "evidence.pdf"
    assert audit_repository.entries[0]["action"] == "document_uploaded"
    assert session.committed is True
    assert len(document_repository.documents) == 1
    assert service.classification_service.entries[0]["predicted_type"] == "evidence"


@pytest.mark.asyncio
async def test_upload_document_rejects_disallowed_file_type() -> None:
    case_id, _, _, _, _, service = build_service_fixture()

    with pytest.raises(HTTPException) as exc_info:
        await service.upload_document(
            case_id=case_id,
            uploaded_by_user_id="user-1",
            file=FakeUploadFile("notes.txt", "text/plain", b"hello"),
        )

    assert exc_info.value.status_code == 400
    assert "not allowed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_replace_document_creates_new_version_and_keeps_old_record() -> None:
    case_id, session, storage, document_repository, audit_repository, service = build_service_fixture()
    original = await document_repository.create(
        {
            "case_id": case_id,
            "uploaded_by_user_id": "user-1",
            "document_type": "passport",
            "original_filename": "passport.pdf",
            "stored_filename": "passport-v1.pdf",
            "storage_backend": "local",
            "storage_key": f"{case_id}/passport-v1.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 10,
            "sha256_hash": hashlib.sha256(b"v1").hexdigest(),
            "document_status": "uploaded",
            "processing_status": "uploaded",
            "classification_label": "passport",
            "classification_source": "manual",
            "file_metadata": {"size_bytes": 10},
            "extracted_metadata": None,
            "version_number": 1,
            "is_current": True,
            "previous_version_id": None,
            "root_document_id": None,
            "replacement_notes": None,
            "uploaded_at": _now(),
        }
    )
    await document_repository.update(original, {"root_document_id": original.id})

    new_document = await service.replace_document(
        document_id=original.id,
        uploaded_by_user_id="user-2",
        file=FakeUploadFile("passport.pdf", "application/pdf", b"v2"),
        replacement_notes="higher quality scan",
    )

    assert len(document_repository.documents) == 2
    assert original.is_current is False
    assert new_document.previous_version_id == original.id
    assert new_document.root_document_id == original.id
    assert new_document.version_number == 2
    assert audit_repository.entries[0]["action"] == "document_replaced"
    assert session.committed is True


@pytest.mark.asyncio
async def test_update_classification_updates_document_type() -> None:
    case_id, session, _, document_repository, _, service = build_service_fixture()
    document = await document_repository.create(
        {
            "case_id": case_id,
            "uploaded_by_user_id": "user-1",
            "document_type": "unclassified",
            "original_filename": "file.pdf",
            "stored_filename": "file-v1.pdf",
            "storage_backend": "local",
            "storage_key": f"{case_id}/file-v1.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 10,
            "sha256_hash": hashlib.sha256(b"v1").hexdigest(),
            "document_status": "uploaded",
            "processing_status": "uploaded",
            "classification_label": None,
            "classification_source": None,
            "classification_confidence_score": None,
            "file_metadata": {"size_bytes": 10},
            "extracted_metadata": None,
            "version_number": 1,
            "is_current": True,
            "previous_version_id": None,
            "root_document_id": None,
            "replacement_notes": None,
            "uploaded_at": _now(),
        }
    )
    await document_repository.update(document, {"root_document_id": document.id})

    updated = await service.update_classification(
        document.id,
        DocumentClassificationUpdate(
            classification_label="passport",
            classification_source="suggested",
            classification_confidence_score=0.87,
            reviewed_by_user_id="reviewer-1",
            review_notes="Filename and text match passport.",
        ),
    )

    assert updated.classification_label == "passport"
    assert updated.classification_source == "suggested"
    assert updated.classification_confidence_score == 0.87
    assert updated.document_type == "passport"
    assert session.committed is True
