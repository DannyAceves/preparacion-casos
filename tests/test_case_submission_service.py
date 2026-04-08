from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.case_submission import (
    CaseCloseRequest,
    CaseSubmissionApproveRequest,
    CaseSubmissionFailRequest,
    CaseSubmissionSubmitRequest,
)
from app.services.case_submission import CaseSubmissionService


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class FakeSession:
    committed: bool = False

    async def commit(self) -> None:
        self.committed = True


@dataclass
class FakeCaseRepository:
    case: object | None

    async def get(self, case_id: uuid.UUID) -> object | None:
        if self.case is not None and self.case.id == case_id:
            return self.case
        return None

    async def update(self, entity: object, data: dict) -> object:
        for key, value in data.items():
            setattr(entity, key, value)
        return entity


@dataclass
class FakeSubmissionRepository:
    item: object | None = None

    async def get_for_case(self, case_id: uuid.UUID) -> object | None:
        if self.item is not None and self.item.case_id == case_id:
            return self.item
        return None

    async def create(self, data: dict) -> object:
        self.item = SimpleNamespace(id=uuid.uuid4(), created_at=_now(), updated_at=_now(), **data)
        return self.item

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


def build_fixture(case_status: str = "draft") -> tuple[uuid.UUID, FakeSession, CaseSubmissionService]:
    case_id = uuid.uuid4()
    session = FakeSession()
    service = CaseSubmissionService(session)
    service.case_repository = FakeCaseRepository(SimpleNamespace(id=case_id, status=case_status))
    service.submission_repository = FakeSubmissionRepository()
    service.audit_log_repository = FakeAuditLogRepository()
    return case_id, session, service


@pytest.mark.asyncio
async def test_approve_for_submission_creates_or_updates_submission(monkeypatch) -> None:
    case_id, session, service = build_fixture()

    async def fake_transition_case(self, incoming_case_id, payload):
        assert incoming_case_id == case_id
        assert payload.target_status == "ready_for_submission"
        service.case_repository.case.status = "ready_for_submission"
        return service.case_repository.case

    monkeypatch.setattr("app.services.case_submission.CaseReadinessService.transition_case", fake_transition_case)

    submission = await service.approve_for_submission(
        case_id,
        CaseSubmissionApproveRequest(approved_by_user_id="attorney-1", notes="Approved to file"),
    )

    assert submission.status == "approved_for_submission"
    assert submission.approved_by_user_id == "attorney-1"
    assert service.audit_log_repository.items[0]["action"] == "case_submission_approved"
    assert session.committed is True


@pytest.mark.asyncio
async def test_submit_requires_prior_approval(monkeypatch) -> None:
    case_id, _, service = build_fixture()
    service.submission_repository.item = SimpleNamespace(
        id=uuid.uuid4(),
        case_id=case_id,
        status="draft",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.submit(
            case_id,
            CaseSubmissionSubmitRequest(submitted_by_user_id="paralegal-1", submission_reference="ABC123"),
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_submit_marks_case_submitted_and_stores_reference(monkeypatch) -> None:
    case_id, session, service = build_fixture(case_status="ready_for_submission")
    service.submission_repository.item = SimpleNamespace(
        id=uuid.uuid4(),
        case_id=case_id,
        status="approved_for_submission",
        created_at=_now(),
        updated_at=_now(),
        approved_for_submission_at=_now(),
        approved_by_user_id="attorney-1",
        submitted_at=None,
        submitted_by_user_id=None,
        submission_reference=None,
        failed_at=None,
        failed_by_user_id=None,
        failure_reason=None,
    )

    async def fake_transition_case(self, incoming_case_id, payload):
        assert incoming_case_id == case_id
        assert payload.target_status == "submitted"
        service.case_repository.case.status = "submitted"
        return service.case_repository.case

    monkeypatch.setattr("app.services.case_submission.CaseReadinessService.transition_case", fake_transition_case)

    submission = await service.submit(
        case_id,
        CaseSubmissionSubmitRequest(
            submitted_by_user_id="paralegal-1",
            submission_reference="ABC123",
            notes="Filed electronically",
        ),
    )

    assert submission.status == "submitted"
    assert submission.submission_reference == "ABC123"
    assert service.audit_log_repository.items[0]["action"] == "case_submitted"
    assert session.committed is True


@pytest.mark.asyncio
async def test_fail_marks_submission_failed() -> None:
    case_id, session, service = build_fixture()

    submission = await service.fail(
        case_id,
        CaseSubmissionFailRequest(failed_by_user_id="paralegal-1", failure_reason="Portal unavailable"),
    )

    assert submission.status == "failed"
    assert submission.failure_reason == "Portal unavailable"
    assert service.audit_log_repository.items[0]["action"] == "case_submission_failed"
    assert session.committed is True


@pytest.mark.asyncio
async def test_close_case_requires_submitted_or_failed_submission() -> None:
    case_id, _, service = build_fixture()

    with pytest.raises(HTTPException) as exc_info:
        await service.close_case(case_id, CaseCloseRequest(closed_by_user_id="attorney-1"))

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_close_case_updates_status_and_audits() -> None:
    case_id, session, service = build_fixture(case_status="submitted")

    updated = await service.close_case(
        case_id,
        CaseCloseRequest(closed_by_user_id="attorney-1", notes="Matter completed"),
    )

    assert updated.status == "closed"
    assert service.audit_log_repository.items[0]["action"] == "case_closed"
    assert session.committed is True
