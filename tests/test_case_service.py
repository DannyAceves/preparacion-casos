from __future__ import annotations

import uuid
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from app.models.case import Case
from app.schemas.case import CaseUpdate
from app.services.case import CaseService


@dataclass
class FakeSession:
    committed: bool = False

    async def get(self, model: type[object], entity_id: uuid.UUID) -> object | None:
        return None

    async def commit(self) -> None:
        self.committed = True


@dataclass
class FakeCaseRepository:
    case: object

    async def get(self, entity_id: uuid.UUID) -> object | None:
        return self.case if self.case.id == entity_id else None

    async def update(self, entity: object, data: dict) -> object:
        for key, value in data.items():
            setattr(entity, key, value)
        return entity


@pytest.mark.asyncio
async def test_case_update_delegates_monitored_status_transition(monkeypatch) -> None:
    case_id = uuid.uuid4()
    session = FakeSession()
    case = SimpleNamespace(id=case_id, client_id=uuid.uuid4(), case_number="CASE-001", case_type="family-based", status="draft", title="Demo Case", summary=None)
    service = CaseService(session)
    service.repository = FakeCaseRepository(case)

    async def fake_transition_case(self, incoming_case_id, payload):
        assert incoming_case_id == case_id
        assert payload.target_status == "ready_for_submission"
        case.status = "ready_for_submission"
        return case

    monkeypatch.setattr("app.services.case.CaseReadinessService.transition_case", fake_transition_case)

    updated = await service.update(case_id, CaseUpdate(status="ready_for_submission"))

    assert updated.status == "ready_for_submission"
