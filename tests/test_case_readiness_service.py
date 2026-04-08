from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.case_readiness import CaseReadinessValidateRequest, CaseTransitionRequest
from app.services.case_readiness import CaseReadinessService


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
class FakeDocumentRepository:
    items: list[object]

    async def list_current_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [item for item in self.items if item.case_id == case_id]


@dataclass
class FakeGeneratedFormRepository:
    items: list[object]

    async def list_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [item for item in self.items if item.case_id == case_id]


@dataclass
class FakeInconsistencyRepository:
    items: list[object]

    async def list_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [item for item in self.items if item.case_id == case_id]


@dataclass
class FakeReviewRepository:
    items: list[object]

    async def list_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [item for item in self.items if item.case_id == case_id]


@dataclass
class FakeAuditLogRepository:
    items: list[dict] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        self.items.append(data)
        return SimpleNamespace(**data)


def build_service_fixture(*, case_status: str = "draft", attorney_approved: bool = False) -> tuple[uuid.UUID, FakeSession, CaseReadinessService]:
    case_id = uuid.uuid4()
    case = SimpleNamespace(id=case_id, status=case_status, case_type="family-based")
    session = FakeSession()
    service = CaseReadinessService(session)
    service.case_repository = FakeCaseRepository(case)
    service.document_repository = FakeDocumentRepository(
        [
            SimpleNamespace(case_id=case_id, document_type="passport", document_status="processed", processing_status="processed"),
            SimpleNamespace(case_id=case_id, document_type="evidence", document_status="processed", processing_status="processed"),
        ]
    )
    service.generated_form_repository = FakeGeneratedFormRepository(
        [
            SimpleNamespace(case_id=case_id, status="approved"),
        ]
    )
    service.inconsistency_repository = FakeInconsistencyRepository(
        [
            SimpleNamespace(case_id=case_id, status="open", severity="critical"),
            SimpleNamespace(case_id=case_id, status="resolved", severity="high"),
        ]
    )
    review_items = []
    if attorney_approved:
        review_items.append(SimpleNamespace(case_id=case_id, review_type="attorney", decision="approved"))
    service.review_repository = FakeReviewRepository(review_items)
    service.audit_log_repository = FakeAuditLogRepository()
    return case_id, session, service


@pytest.mark.asyncio
async def test_get_readiness_reports_missing_documents_and_critical_inconsistencies() -> None:
    case_id, _, service = build_service_fixture()

    readiness = await service.get_readiness(case_id)

    assert readiness.summary.missing_required_document_types == ["birth_certificate", "marriage_certificate"]
    assert readiness.summary.open_critical_inconsistency_count == 1
    ready_for_submission = next(item for item in readiness.targets if item.target_status == "ready_for_submission")
    assert ready_for_submission.is_ready is False
    assert any(item.code == "missing_required_documents" for item in ready_for_submission.blockers)
    assert any(item.code == "open_critical_inconsistencies" for item in ready_for_submission.blockers)


@pytest.mark.asyncio
async def test_validate_readiness_audits() -> None:
    case_id, session, service = build_service_fixture()

    readiness = await service.validate_readiness(case_id, CaseReadinessValidateRequest(actor_reference="qa-1"))

    assert readiness.case_id == case_id
    assert service.audit_log_repository.items[0]["action"] == "case_readiness_validated"
    assert session.committed is True


@pytest.mark.asyncio
async def test_transition_case_blocks_invalid_ready_for_submission() -> None:
    case_id, _, service = build_service_fixture()

    with pytest.raises(HTTPException) as exc_info:
        await service.transition_case(
            case_id,
            CaseTransitionRequest(target_status="ready_for_submission", actor_reference="paralegal-1"),
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_transition_case_allows_submitted_when_ready_and_audits() -> None:
    case_id, session, service = build_service_fixture(case_status="ready_for_submission", attorney_approved=True)
    service.document_repository.items.extend(
        [
            SimpleNamespace(case_id=case_id, document_type="birth_certificate", document_status="processed", processing_status="processed"),
            SimpleNamespace(case_id=case_id, document_type="marriage_certificate", document_status="processed", processing_status="processed"),
        ]
    )
    service.inconsistency_repository.items = []

    updated = await service.transition_case(
        case_id,
        CaseTransitionRequest(target_status="submitted", actor_reference="attorney-1", notes="Ready to file"),
    )

    assert updated.status == "submitted"
    assert service.audit_log_repository.items[0]["action"] == "case_status_transitioned"
    assert service.audit_log_repository.items[0]["payload"]["from_status"] == "ready_for_submission"
    assert session.committed is True
