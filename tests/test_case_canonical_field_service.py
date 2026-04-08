from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.case import Case
from app.models.document import Document
from app.schemas.case_canonical_field import CaseCanonicalFieldPatchRequest
from app.services.case_canonical_field import CaseCanonicalFieldService


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class FakeSession:
    cases: dict[uuid.UUID, object]
    documents: dict[uuid.UUID, object]
    committed: bool = False

    async def get(self, model: type[object], entity_id: uuid.UUID) -> object | None:
        if model is Case:
            return self.cases.get(entity_id)
        if model is Document:
            return self.documents.get(entity_id)
        return None

    async def commit(self) -> None:
        self.committed = True


@dataclass
class FakeCanonicalFieldRepository:
    fields: list[object] = field(default_factory=list)

    async def list_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [item for item in self.fields if item.case_id == case_id]

    async def get_by_case_and_field_key(self, case_id: uuid.UUID, field_key: str) -> object | None:
        for item in self.fields:
            if item.case_id == case_id and item.field_key == field_key:
                return item
        return None

    async def create(self, data: dict) -> object:
        entity = SimpleNamespace(id=uuid.uuid4(), created_at=_now(), updated_at=_now(), **data)
        self.fields.append(entity)
        return entity

    async def update(self, entity: object, data: dict) -> object:
        for key, value in data.items():
            setattr(entity, key, value)
        entity.updated_at = _now()
        return entity


@dataclass
class FakeAuditLogRepository:
    entries: list[dict] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        self.entries.append(data)
        return SimpleNamespace(**data)


def build_fixture():
    case_id = uuid.uuid4()
    document_id = uuid.uuid4()
    session = FakeSession(
        cases={case_id: SimpleNamespace(id=case_id, case_type="family-based")},
        documents={document_id: SimpleNamespace(id=document_id, case_id=case_id)},
    )
    service = CaseCanonicalFieldService(session)
    service.repository = FakeCanonicalFieldRepository()
    service.audit_log_repository = FakeAuditLogRepository()
    return case_id, document_id, session, service


@pytest.mark.asyncio
async def test_list_case_canonical_fields_returns_case_fields() -> None:
    case_id, _, _, service = build_fixture()
    service.repository.fields.append(
        SimpleNamespace(
            id=uuid.uuid4(),
            case_id=case_id,
            source_document_id=None,
            field_key="beneficiary.full_name",
            field_value="Demo Applicant",
            confidence_score=0.9,
            source_priority=100,
            status="approved",
            created_at=_now(),
            updated_at=_now(),
        )
    )

    results = await service.list_for_case(case_id)

    assert len(results) == 1
    assert results[0].field_key == "beneficiary.full_name"


@pytest.mark.asyncio
async def test_upsert_creates_single_field_and_audits() -> None:
    case_id, document_id, session, service = build_fixture()

    created = await service.upsert_by_field_key(
        case_id=case_id,
        field_key="beneficiary.full_name",
        payload=CaseCanonicalFieldPatchRequest(
            actor_reference="lawyer-1",
            source_document_id=document_id,
            field_value="Demo Applicant",
            confidence_score=0.98,
            source_priority=100,
            status="approved",
        ),
    )

    assert created.field_key == "beneficiary.full_name"
    assert len(service.repository.fields) == 1
    assert service.audit_log_repository.entries[0]["action"] == "canonical_field_created"
    assert session.committed is True


@pytest.mark.asyncio
async def test_upsert_updates_existing_without_duplicates() -> None:
    case_id, _, session, service = build_fixture()
    existing = SimpleNamespace(
        id=uuid.uuid4(),
        case_id=case_id,
        source_document_id=None,
        field_key="beneficiary.full_name",
        field_value="Old Name",
        confidence_score=0.5,
        source_priority=10,
        status="suggested",
        created_at=_now(),
        updated_at=_now(),
    )
    service.repository.fields.append(existing)

    updated = await service.upsert_by_field_key(
        case_id=case_id,
        field_key="beneficiary.full_name",
        payload=CaseCanonicalFieldPatchRequest(
            actor_reference="lawyer-2",
            field_value="New Name",
            status="confirmed",
        ),
    )

    assert len(service.repository.fields) == 1
    assert updated.field_value == "New Name"
    assert updated.status == "confirmed"
    assert service.audit_log_repository.entries[0]["action"] == "canonical_field_updated"
    assert session.committed is True


@pytest.mark.asyncio
async def test_upsert_rejects_invalid_status() -> None:
    case_id, _, _, service = build_fixture()

    with pytest.raises(HTTPException) as exc_info:
        await service.upsert_by_field_key(
            case_id=case_id,
            field_key="beneficiary.full_name",
            payload=CaseCanonicalFieldPatchRequest.model_construct(  # bypass schema literal to hit service rule
                actor_reference="lawyer-1",
                field_value="Name",
                status="invalid",
            ),
        )

    assert exc_info.value.status_code == 400
    assert "invalid canonical field status" in exc_info.value.detail
