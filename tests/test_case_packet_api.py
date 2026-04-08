from __future__ import annotations

import os
import uuid

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.api.deps import get_session_dependency
from app.main import app
from app.services.case_packet import CasePacketService


def test_generate_case_packet_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()
    packet_id = uuid.uuid4()

    async def fake_generate_for_case(self, incoming_case_id, payload):
        assert incoming_case_id == case_id
        assert payload.generated_by_reference == "qa-1"
        return {
            "id": str(packet_id),
            "case_id": str(case_id),
            "packet_version": 1,
            "packet_status": "generated",
            "generated_by_reference": "qa-1",
            "summary_payload": {
                "case_id": str(case_id),
                "case_number": "CASE-001",
                "case_type": "family-based",
                "case_status": "draft",
                "title": "Demo Case",
                "client": {"id": str(uuid.uuid4()), "full_name": "Demo Applicant", "email": "demo@example.com", "phone": "+52"},
                "participants": [],
                "canonical_fields": [],
                "open_inconsistency_count": 0,
                "latest_review": None,
            },
            "document_index": [],
            "checklist_payload": [],
            "export_artifact": {
                "artifact_type": "case_review_packet",
                "format": "json",
                "generated_at": "2026-04-02T00:00:00Z",
                "packet_version": 1,
                "sections": [],
                "prefilled_forms_placeholder": {"ready": False, "available_templates": []},
            },
            "generation_notes": "Initial packet",
            "generated_at": "2026-04-02T00:00:00Z",
            "created_at": "2026-04-02T00:00:00Z",
            "updated_at": "2026-04-02T00:00:00Z",
        }

    monkeypatch.setattr(CasePacketService, "generate_for_case", fake_generate_for_case)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/cases/{case_id}/packet/generate",
            json={"generated_by_reference": "qa-1", "generation_notes": "Initial packet"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["id"] == str(packet_id)


def test_get_case_packet_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()

    async def fake_get_latest_for_case(self, incoming_case_id):
        assert incoming_case_id == case_id
        return {
            "id": str(uuid.uuid4()),
            "case_id": str(case_id),
            "packet_version": 2,
            "packet_status": "generated",
            "generated_by_reference": "paralegal-1",
            "summary_payload": {
                "case_id": str(case_id),
                "case_number": "CASE-001",
                "case_type": "family-based",
                "case_status": "draft",
                "title": "Demo Case",
                "client": {"id": str(uuid.uuid4()), "full_name": "Demo Applicant", "email": "demo@example.com", "phone": "+52"},
                "participants": [],
                "canonical_fields": [],
                "open_inconsistency_count": 1,
                "latest_review": None,
            },
            "document_index": [],
            "checklist_payload": [],
            "export_artifact": {
                "artifact_type": "case_review_packet",
                "format": "json",
                "generated_at": "2026-04-02T00:00:00Z",
                "packet_version": 2,
                "sections": [],
                "prefilled_forms_placeholder": {"ready": False, "available_templates": []},
            },
            "generation_notes": None,
            "generated_at": "2026-04-02T00:00:00Z",
            "created_at": "2026-04-02T00:00:00Z",
            "updated_at": "2026-04-02T00:00:00Z",
        }

    monkeypatch.setattr(CasePacketService, "get_latest_for_case", fake_get_latest_for_case)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.get(f"/api/v1/cases/{case_id}/packet")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["packet_version"] == 2
