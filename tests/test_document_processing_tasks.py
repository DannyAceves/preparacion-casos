from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.services.document_processing_tasks import DocumentProcessingTaskService
from app.services.document_text_extraction import TextExtractionResult


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class FakeSession:
    committed: bool = False

    async def commit(self) -> None:
        self.committed = True


@dataclass
class FakeDocumentRepository:
    document: object

    async def get(self, document_id: uuid.UUID) -> object | None:
        return self.document if self.document.id == document_id else None

    async def update(self, entity: object, data: dict) -> object:
        for key, value in data.items():
            setattr(entity, key, value)
        entity.updated_at = _now()
        return entity


@dataclass
class FakeAuditLogRepository:
    items: list[dict] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        self.items.append(data)
        return SimpleNamespace(**data)


class FakeTextExtractionService:
    def __init__(self, result: TextExtractionResult) -> None:
        self.result = result
        self.field_detector = SimpleNamespace(detect=lambda text: {"raw_text_length": len(text)})

    def extract_for_document(self, **kwargs) -> TextExtractionResult:
        return self.result


@dataclass
class FakeClassificationResult:
    classification: object
    idempotent: bool = False


@dataclass
class FakeClassificationService:
    result_type: str = "passport"
    confidence_score: float = 0.91
    source: str = "automatic"
    method: str = "filename_rules"
    calls: list[dict] = field(default_factory=list)

    async def classify_document(self, *, document: object, actor_reference: str | None, trigger: str | None, force_reprocess: bool = False) -> FakeClassificationResult:
        self.calls.append(
            {
                "document_id": document.id,
                "actor_reference": actor_reference,
                "trigger": trigger,
                "force_reprocess": force_reprocess,
            }
        )
        document.classification_label = self.result_type
        document.classification_source = self.source
        document.classification_confidence_score = self.confidence_score
        document.document_type = self.result_type
        return FakeClassificationResult(
            classification=SimpleNamespace(
                predicted_type=self.result_type,
                confidence_score=self.confidence_score,
                classification_source=self.source,
                classification_method=self.method,
            )
        )


@pytest.mark.asyncio
async def test_ocr_document_persists_text_and_audits() -> None:
    document_id = uuid.uuid4()
    document = SimpleNamespace(
        id=document_id,
        case_id=uuid.uuid4(),
        storage_backend="local",
        storage_key="case/doc.pdf",
        mime_type="application/pdf",
        original_filename="doc.pdf",
        extracted_text=None,
        extracted_fields=None,
        extracted_metadata=None,
        document_status="uploaded",
        updated_at=_now(),
    )
    session = FakeSession()
    service = DocumentProcessingTaskService(
        session,
        text_extraction_service=FakeTextExtractionService(
            TextExtractionResult(
                requires_ocr=False,
                extracted_text="Extracted searchable text",
                extracted_fields={"raw_text_length": 25},
                extraction_method="embedded_pdf_text",
            )
        ),
    )
    service.document_repository = FakeDocumentRepository(document)
    service.audit_log_repository = FakeAuditLogRepository()
    service.classification_service = FakeClassificationService()

    payload = await service.ocr_document(document_id, job_payload={"trigger": "automatic_upload"})

    assert payload["ocr_status"] == "completed"
    assert document.extracted_text == "Extracted searchable text"
    assert service.audit_log_repository.items[0]["action"] == "document_text_extracted"
    assert session.committed is True


@pytest.mark.asyncio
async def test_extract_document_fields_marks_manual_review_without_text() -> None:
    document_id = uuid.uuid4()
    document = SimpleNamespace(
        id=document_id,
        case_id=uuid.uuid4(),
        extracted_text=None,
        extracted_fields=None,
        extracted_metadata=None,
        document_status="uploaded",
        updated_at=_now(),
    )
    session = FakeSession()
    service = DocumentProcessingTaskService(
        session,
        text_extraction_service=FakeTextExtractionService(
            TextExtractionResult(
                requires_ocr=True,
                extracted_text=None,
                extracted_fields={},
                extraction_method="ocrmypdf",
                manual_review_required=True,
                error_message="ocr failed",
            )
        ),
    )
    service.document_repository = FakeDocumentRepository(document)
    service.audit_log_repository = FakeAuditLogRepository()
    service.classification_service = FakeClassificationService()

    payload = await service.extract_document_fields(document_id, job_payload={"trigger": "manual_reprocess"})

    assert payload["field_extraction_status"] == "manual_review"
    assert document.document_status == "manual_review"
    assert service.audit_log_repository.items[0]["action"] == "document_field_extraction_manual_review"


@pytest.mark.asyncio
async def test_classify_document_persists_automatic_classification_metadata() -> None:
    document_id = uuid.uuid4()
    document = SimpleNamespace(
        id=document_id,
        case_id=uuid.uuid4(),
        classification_label=None,
        classification_source=None,
        classification_confidence_score=None,
        document_type="unclassified",
        extracted_metadata=None,
        updated_at=_now(),
    )
    session = FakeSession()
    service = DocumentProcessingTaskService(
        session,
        text_extraction_service=FakeTextExtractionService(
            TextExtractionResult(
                requires_ocr=False,
                extracted_text="passport text",
                extracted_fields={},
                extraction_method="embedded_pdf_text",
            )
        ),
    )
    service.document_repository = FakeDocumentRepository(document)
    service.audit_log_repository = FakeAuditLogRepository()
    service.classification_service = FakeClassificationService()

    payload = await service.classify_document(document_id, job_payload={"trigger": "automatic_upload"})

    assert payload["classification_status"] == "completed"
    assert payload["predicted_type"] == "passport"
    assert document.classification_label == "passport"
    assert document.extracted_metadata["classification_status"] == "completed"
    assert session.committed is True
