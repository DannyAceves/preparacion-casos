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

from app.schemas.document import DocumentClassificationUpdate
from app.services.document_classification import DocumentClassificationService, RuleBasedDocumentClassifier


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class FakeSession:
    async def flush(self) -> None:
        return None


@dataclass
class FakeDocumentRepository:
    async def update(self, entity: object, data: dict) -> object:
        for key, value in data.items():
            setattr(entity, key, value)
        entity.updated_at = _now()
        return entity


@dataclass
class FakeDocumentClassificationRepository:
    items: list[object] = field(default_factory=list)

    async def get_active_for_document(self, document_id: uuid.UUID) -> object | None:
        active = [item for item in self.items if item.document_id == document_id and item.is_active]
        active.sort(key=lambda item: item.created_at, reverse=True)
        return active[0] if active else None

    async def list_for_document(self, document_id: uuid.UUID) -> list[object]:
        items = [item for item in self.items if item.document_id == document_id]
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    async def deactivate_active_for_document(self, document_id: uuid.UUID) -> list[object]:
        active_items = [item for item in self.items if item.document_id == document_id and item.is_active]
        for item in active_items:
            item.is_active = False
            item.updated_at = _now()
        return active_items

    async def create(self, data: dict) -> object:
        item = SimpleNamespace(id=uuid.uuid4(), created_at=_now(), updated_at=_now(), **data)
        self.items.append(item)
        return item


@dataclass
class FakeAuditLogRepository:
    items: list[dict] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        self.items.append(data)
        return SimpleNamespace(**data)


def build_service() -> tuple[DocumentClassificationService, FakeDocumentClassificationRepository, FakeAuditLogRepository]:
    session = FakeSession()
    service = DocumentClassificationService(session)
    service.document_repository = FakeDocumentRepository()
    classification_repository = FakeDocumentClassificationRepository()
    audit_repository = FakeAuditLogRepository()
    service.classification_repository = classification_repository
    service.audit_log_repository = audit_repository
    return service, classification_repository, audit_repository


def build_document(*, filename: str, extracted_text: str | None = None) -> object:
    return SimpleNamespace(
        id=uuid.uuid4(),
        case_id=uuid.uuid4(),
        version_number=1,
        original_filename=filename,
        extracted_text=extracted_text,
        classification_label=None,
        classification_source=None,
        classification_confidence_score=None,
        document_type="unclassified",
        updated_at=_now(),
    )


def test_rule_based_classifier_prefers_strong_filename_match() -> None:
    classifier = RuleBasedDocumentClassifier()
    document = build_document(filename="passport_scan.pdf", extracted_text=None)

    result = classifier.classify(document)

    assert result.predicted_type == "passport"
    assert result.confidence_score >= 0.82
    assert result.classification_method == "filename_rules"


@pytest.mark.asyncio
async def test_classify_document_creates_automatic_classification_record() -> None:
    service, classification_repository, audit_repository = build_service()
    document = build_document(
        filename="document.pdf",
        extracted_text="Passport number 12345 nationality Mexico date of birth 1990-01-01",
    )

    result = await service.classify_document(
        document=document,
        actor_reference="worker",
        trigger="automatic_upload",
    )

    assert result.idempotent is False
    assert result.classification.predicted_type == "passport"
    assert document.classification_label == "passport"
    assert document.classification_source == "automatic"
    assert classification_repository.items[0].is_active is True
    assert audit_repository.items[0]["action"] == "document_classified"


@pytest.mark.asyncio
async def test_review_document_classification_creates_manual_override() -> None:
    service, classification_repository, audit_repository = build_service()
    document = build_document(filename="misc.pdf")

    await service.classify_document(
        document=document,
        actor_reference="worker",
        trigger="automatic_upload",
    )
    updated = await service.review_document_classification(
        document=document,
        payload=DocumentClassificationUpdate(
            classification_label="evidence",
            classification_source="manual",
            classification_confidence_score=1.0,
            reviewed_by_user_id="reviewer-1",
            review_notes="Attorney override.",
        ),
    )

    assert updated.predicted_type == "evidence"
    assert updated.is_override is True
    assert document.classification_label == "evidence"
    assert document.classification_source == "manual"
    assert len(classification_repository.items) == 2
    assert classification_repository.items[0].is_active is False
    assert classification_repository.items[1].is_active is True
    assert audit_repository.items[-1]["action"] == "document_classification_overridden"
