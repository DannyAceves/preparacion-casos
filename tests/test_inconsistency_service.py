from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.case import Case
from app.schemas.inconsistency import InconsistencyActionRequest, InconsistencyCreateRequest
from app.services.inconsistency import InconsistencyService


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
class FakeInconsistencyRepository:
    items: list[object] = field(default_factory=list)

    async def list_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [item for item in self.items if item.case_id == case_id]

    async def get_for_case(self, case_id: uuid.UUID, inconsistency_id: uuid.UUID) -> object | None:
        for item in self.items:
            if item.case_id == case_id and item.id == inconsistency_id:
                return item
        return None

    async def create(self, data: dict) -> object:
        entity = SimpleNamespace(id=uuid.uuid4(), created_at=_now(), updated_at=_now(), **data)
        self.items.append(entity)
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
    session = FakeSession(cases={case_id: SimpleNamespace(id=case_id, case_type="family-based")})
    service = InconsistencyService(session)
    service.repository = FakeInconsistencyRepository()
    service.audit_log_repository = FakeAuditLogRepository()
    return case_id, session, service


@pytest.mark.asyncio
async def test_list_case_inconsistencies_returns_case_items() -> None:
    case_id, _, service = build_fixture()
    service.repository.items.append(
        SimpleNamespace(
            id=uuid.uuid4(),
            case_id=case_id,
            field_key="beneficiary.date_of_birth",
            severity="high",
            status="open",
            description="Mismatch between questionnaire and passport",
            evidence_payload={"sources": ["questionnaire", "passport"]},
            resolution_notes=None,
            resolved_by_user_id=None,
            resolved_at=None,
            created_at=_now(),
            updated_at=_now(),
        )
    )

    result = await service.list_for_case(case_id)

    assert len(result) == 1
    assert result[0].field_key == "beneficiary.date_of_birth"


@pytest.mark.asyncio
async def test_create_inconsistency_audits() -> None:
    case_id, session, service = build_fixture()

    created = await service.create_for_case(
        case_id,
        InconsistencyCreateRequest(
            field_key="beneficiary.date_of_birth",
            severity="critical",
            status="open",
            description="DOB differs between sources",
            evidence_payload={"sources": ["passport", "questionnaire"]},
            actor_reference="system-detector",
        ),
    )

    assert created.severity == "critical"
    assert created.status == "open"
    assert service.audit_log_repository.entries[0]["action"] == "inconsistency_created"
    assert session.committed is True


@pytest.mark.asyncio
async def test_create_inconsistency_rejects_invalid_severity() -> None:
    case_id, _, service = build_fixture()

    with pytest.raises(HTTPException) as exc_info:
        await service.create_for_case(
            case_id,
            InconsistencyCreateRequest.model_construct(
                field_key="beneficiary.date_of_birth",
                severity="invalid",
                status="open",
                description="bad",
                evidence_payload=None,
                actor_reference=None,
            ),
        )

    assert exc_info.value.status_code == 400
    assert "invalid inconsistency severity" in exc_info.value.detail


@pytest.mark.asyncio
async def test_resolve_inconsistency_updates_status_and_audits() -> None:
    case_id, session, service = build_fixture()
    inconsistency = SimpleNamespace(
        id=uuid.uuid4(),
        case_id=case_id,
        field_key="beneficiary.date_of_birth",
        severity="high",
        status="open",
        description="Mismatch",
        evidence_payload=None,
        resolution_notes=None,
        resolved_by_user_id=None,
        resolved_at=None,
        created_at=_now(),
        updated_at=_now(),
    )
    service.repository.items.append(inconsistency)

    resolved = await service.resolve_for_case(
        case_id,
        inconsistency.id,
        InconsistencyActionRequest(actor_reference="lawyer-1", notes="Verified passport as source of truth"),
    )

    assert resolved.status == "resolved"
    assert resolved.resolution_notes == "Verified passport as source of truth"
    assert service.audit_log_repository.entries[0]["action"] == "inconsistency_resolved"
    assert session.committed is True


@pytest.mark.asyncio
async def test_dismiss_inconsistency_updates_status_and_audits() -> None:
    case_id, session, service = build_fixture()
    inconsistency = SimpleNamespace(
        id=uuid.uuid4(),
        case_id=case_id,
        field_key="beneficiary.middle_name",
        severity="low",
        status="under_review",
        description="Minor formatting mismatch",
        evidence_payload=None,
        resolution_notes=None,
        resolved_by_user_id=None,
        resolved_at=None,
        created_at=_now(),
        updated_at=_now(),
    )
    service.repository.items.append(inconsistency)

    dismissed = await service.dismiss_for_case(
        case_id,
        inconsistency.id,
        InconsistencyActionRequest(actor_reference="lawyer-2", notes="Not material to filing"),
    )

    assert dismissed.status == "dismissed"
    assert dismissed.resolution_notes == "Not material to filing"
    assert service.audit_log_repository.entries[0]["action"] == "inconsistency_dismissed"
    assert session.committed is True
