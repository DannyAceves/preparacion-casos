from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.case import Case
from app.schemas.review import CaseReviewCreateRequest
from app.services.review import ReviewService


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
class FakeReviewRepository:
    items: list[object] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        entity = SimpleNamespace(id=uuid.uuid4(), created_at=_now(), updated_at=_now(), **data)
        self.items.append(entity)
        return entity

    async def list_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [item for item in self.items if item.case_id == case_id]


@dataclass
class FakeAuditLogRepository:
    items: list[object] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        entity = SimpleNamespace(id=uuid.uuid4(), **data)
        self.items.append(entity)
        return entity

    async def list_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [item for item in self.items if item.case_id == case_id]


def build_fixture():
    case_id = uuid.uuid4()
    session = FakeSession(cases={case_id: SimpleNamespace(id=case_id)})
    service = ReviewService(session)
    service.review_repository = FakeReviewRepository()
    service.audit_log_repository = FakeAuditLogRepository()
    return case_id, session, service


@pytest.mark.asyncio
async def test_create_review_for_case_audits() -> None:
    case_id, session, service = build_fixture()

    review = await service.create_for_case(
        case_id,
        CaseReviewCreateRequest(
            review_type="attorney",
            reviewer_reference="attorney-1",
            decision="approved",
            notes="Package is complete",
            actor_reference="attorney-1",
        ),
    )

    assert review.review_type == "attorney"
    assert review.decision == "approved"
    assert service.audit_log_repository.items[0].action == "review_created"
    assert session.committed is True


@pytest.mark.asyncio
async def test_create_review_rejects_invalid_case() -> None:
    _, _, service = build_fixture()

    with pytest.raises(HTTPException) as exc_info:
        await service.create_for_case(
            uuid.uuid4(),
            CaseReviewCreateRequest(
                review_type="qa",
                reviewer_reference="qa-1",
                decision="rejected",
            ),
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_timeline_combines_reviews_and_audit_logs() -> None:
    case_id, _, service = build_fixture()
    review_time = datetime(2026, 4, 2, 10, 0, tzinfo=UTC)
    audit_time = datetime(2026, 4, 2, 12, 0, tzinfo=UTC)
    service.review_repository.items.append(
        SimpleNamespace(
            id=uuid.uuid4(),
            case_id=case_id,
            review_type="paralegal",
            reviewer_reference="paralegal-1",
            decision="fix_required",
            notes="Missing signature page",
            reviewed_at=review_time,
            created_at=review_time,
        )
    )
    service.audit_log_repository.items.append(
        SimpleNamespace(
            id=uuid.uuid4(),
            case_id=case_id,
            entity_type="document",
            entity_id=str(uuid.uuid4()),
            action="document_uploaded",
            actor_reference="user-1",
            payload={"case_id": str(case_id)},
            occurred_at=audit_time,
        )
    )

    timeline = await service.get_case_timeline(case_id)

    assert len(timeline) == 2
    assert timeline[0].event_type == "audit_log"
    assert timeline[1].event_type == "review"
