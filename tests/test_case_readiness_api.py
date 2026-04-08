from __future__ import annotations

import os
import uuid

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.api.deps import get_session_dependency
from app.main import app
from app.services.case_readiness import CaseReadinessService


def test_get_case_readiness_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()

    async def fake_get_readiness(self, incoming_case_id):
        assert incoming_case_id == case_id
        return {
            "case_id": str(case_id),
            "case_status": "draft",
            "summary": {
                "required_document_types": ["passport"],
                "present_required_document_types": [],
                "missing_required_document_types": ["passport"],
                "open_high_or_critical_inconsistency_count": 1,
                "open_critical_inconsistency_count": 1,
                "unapproved_generated_form_count": 1,
                "generated_form_count": 1,
                "attorney_approved_review_exists": False,
            },
            "targets": [
                {
                    "target_status": "attorney_review",
                    "is_ready": False,
                    "blockers": [{"code": "missing_required_documents", "message": "missing", "severity": "blocking"}],
                    "warnings": [],
                }
            ],
        }

    monkeypatch.setattr(CaseReadinessService, "get_readiness", fake_get_readiness)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.get(f"/api/v1/cases/{case_id}/readiness")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["case_id"] == str(case_id)


def test_transition_case_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()

    async def fake_transition_case(self, incoming_case_id, payload):
        assert incoming_case_id == case_id
        assert payload.target_status == "submitted"
        return {
            "id": str(case_id),
            "client_id": str(uuid.uuid4()),
            "case_number": "CASE-001",
            "case_type": "family-based",
            "status": "submitted",
            "title": "Demo Case",
            "summary": None,
            "created_at": "2026-04-02T00:00:00Z",
            "updated_at": "2026-04-02T00:00:00Z",
        }

    monkeypatch.setattr(CaseReadinessService, "transition_case", fake_transition_case)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/cases/{case_id}/transition",
            json={"target_status": "submitted", "actor_reference": "attorney-1"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "submitted"
