from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.case_packet import CasePacketGenerateRequest
from app.services.case_packet import CasePacketService


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class FakeSession:
    committed: bool = False

    async def commit(self) -> None:
        self.committed = True


@dataclass
class FakeCasePacketRepository:
    items: list[object] = field(default_factory=list)

    async def get_latest_for_case(self, case_id: uuid.UUID) -> object | None:
        packets = [item for item in self.items if item.case_id == case_id]
        packets.sort(key=lambda item: item.packet_version, reverse=True)
        return packets[0] if packets else None

    async def create(self, data: dict) -> object:
        packet = SimpleNamespace(id=uuid.uuid4(), created_at=_now(), updated_at=_now(), **data)
        self.items.append(packet)
        return packet


@dataclass
class FakeDocumentRepository:
    items: list[object]

    async def list_current_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [item for item in self.items if item.case_id == case_id and item.is_current]


@dataclass
class FakeCanonicalFieldRepository:
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
        reviews = [item for item in self.items if item.case_id == case_id]
        reviews.sort(key=lambda item: item.reviewed_at, reverse=True)
        return reviews


@dataclass
class FakeAuditLogRepository:
    items: list[dict] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        self.items.append(data)
        return SimpleNamespace(**data)


def build_fixture() -> tuple[uuid.UUID, FakeSession, CasePacketService]:
    case_id = uuid.uuid4()
    session = FakeSession()
    service = CasePacketService(session)
    service.case_packet_repository = FakeCasePacketRepository()
    service.document_repository = FakeDocumentRepository(
        [
            SimpleNamespace(
                id=uuid.uuid4(),
                case_id=case_id,
                is_current=True,
                document_type="evidence",
                original_filename="proof.pdf",
                classification_label="evidence",
                classification_confidence_score=0.88,
                document_status="processed",
                processing_status="processed",
                uploaded_at=_now(),
            ),
            SimpleNamespace(
                id=uuid.uuid4(),
                case_id=case_id,
                is_current=True,
                document_type="passport",
                original_filename="passport.pdf",
                classification_label="passport",
                classification_confidence_score=0.97,
                document_status="processed",
                processing_status="processed",
                uploaded_at=_now(),
            ),
            SimpleNamespace(
                id=uuid.uuid4(),
                case_id=case_id,
                is_current=True,
                document_type="birth_certificate",
                original_filename="birth.pdf",
                classification_label="birth_certificate",
                classification_confidence_score=0.92,
                document_status="rejected",
                processing_status="processed",
                uploaded_at=_now(),
            ),
        ]
    )
    service.canonical_field_repository = FakeCanonicalFieldRepository(
        [
            SimpleNamespace(
                case_id=case_id,
                field_key="beneficiary.full_name",
                field_value="Demo Applicant",
                status="approved",
                confidence_score=Decimal("0.9800"),
            ),
            SimpleNamespace(
                case_id=case_id,
                field_key="beneficiary.dob",
                field_value="1990-01-01",
                status="suggested",
                confidence_score=Decimal("0.8100"),
            ),
        ]
    )
    service.inconsistency_repository = FakeInconsistencyRepository(
        [
            SimpleNamespace(case_id=case_id, status="open"),
            SimpleNamespace(case_id=case_id, status="resolved"),
        ]
    )
    service.review_repository = FakeReviewRepository(
        [
            SimpleNamespace(
                case_id=case_id,
                review_type="attorney",
                decision="approved",
                reviewed_at=_now(),
                reviewer_reference="attorney-1",
            )
        ]
    )
    service.audit_log_repository = FakeAuditLogRepository()

    client = SimpleNamespace(id=uuid.uuid4(), first_name="Demo", last_name="Applicant", email="demo@example.com", phone="+52")
    case = SimpleNamespace(
        id=case_id,
        client=client,
        case_number="CASE-001",
        case_type="family-based",
        status="draft",
        title="Demo Case",
    )

    async def fake_get_case(incoming_case_id: uuid.UUID):
        if incoming_case_id != case_id:
            raise HTTPException(status_code=404, detail="case not found")
        return case

    async def fake_list_participants(incoming_case_id: uuid.UUID):
        assert incoming_case_id == case_id
        return [
            SimpleNamespace(
                id=uuid.uuid4(),
                role="beneficiary",
                first_name="Demo",
                last_name="Applicant",
                email="demo@example.com",
            )
        ]

    service._get_case = fake_get_case
    service._list_participants = fake_list_participants
    return case_id, session, service


@pytest.mark.asyncio
async def test_generate_case_packet_builds_sorted_index_and_summary() -> None:
    case_id, session, service = build_fixture()

    packet = await service.generate_for_case(
        case_id,
        CasePacketGenerateRequest(generated_by_reference="paralegal-1", generation_notes="Initial packet"),
    )

    assert packet.packet_version == 1
    assert packet.document_index[0]["document_type"] == "passport"
    assert len(packet.document_index) == 2
    assert packet.summary_payload["open_inconsistency_count"] == 1
    assert packet.checklist_payload[-1]["status"] == "warning"
    assert packet.export_artifact["artifact_type"] == "case_review_packet"
    assert service.audit_log_repository.items[0]["action"] == "case_packet_generated"
    assert session.committed is True


@pytest.mark.asyncio
async def test_get_latest_case_packet_returns_most_recent_version() -> None:
    case_id, _, service = build_fixture()
    service.case_packet_repository.items.extend(
        [
            SimpleNamespace(case_id=case_id, packet_version=1, generated_at=_now()),
            SimpleNamespace(case_id=case_id, packet_version=2, generated_at=_now()),
        ]
    )

    packet = await service.get_latest_for_case(case_id)

    assert packet.packet_version == 2


@pytest.mark.asyncio
async def test_get_latest_case_packet_rejects_missing_case() -> None:
    _, _, service = build_fixture()

    with pytest.raises(HTTPException) as exc_info:
        await service.get_latest_for_case(uuid.uuid4())

    assert exc_info.value.status_code == 404
