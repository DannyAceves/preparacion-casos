from __future__ import annotations

import os
import uuid

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.api.deps import get_session_dependency
from app.main import app
from app.services.case_submission import CaseSubmissionService


def test_get_case_submission_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()
    submission_id = uuid.uuid4()

    async def fake_get_for_case(self, incoming_case_id):
        assert incoming_case_id == case_id
        return {
            "id": str(submission_id),
            "case_id": str(case_id),
            "status": "approved_for_submission",
            "approved_for_submission_at": "2026-04-02T00:00:00Z",
            "approved_by_user_id": "attorney-1",
            "submitted_at": None,
            "submitted_by_user_id": None,
            "submission_reference": None,
            "failed_at": None,
            "failed_by_user_id": None,
            "failure_reason": None,
            "created_at": "2026-04-02T00:00:00Z",
            "updated_at": "2026-04-02T00:00:00Z",
        }

    monkeypatch.setattr(CaseSubmissionService, "get_for_case", fake_get_for_case)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.get(f"/api/v1/cases/{case_id}/submission")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "approved_for_submission"


def test_submit_case_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()

    async def fake_submit(self, incoming_case_id, payload):
        assert incoming_case_id == case_id
        assert payload.submission_reference == "ABC123"
        return {
            "id": str(uuid.uuid4()),
            "case_id": str(case_id),
            "status": "submitted",
            "approved_for_submission_at": "2026-04-02T00:00:00Z",
            "approved_by_user_id": "attorney-1",
            "submitted_at": "2026-04-02T01:00:00Z",
            "submitted_by_user_id": "paralegal-1",
            "submission_reference": "ABC123",
            "failed_at": None,
            "failed_by_user_id": None,
            "failure_reason": None,
            "created_at": "2026-04-02T00:00:00Z",
            "updated_at": "2026-04-02T01:00:00Z",
        }

    monkeypatch.setattr(CaseSubmissionService, "submit", fake_submit)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/cases/{case_id}/submission/submit",
            json={"submitted_by_user_id": "paralegal-1", "submission_reference": "ABC123"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["submission_reference"] == "ABC123"
