from __future__ import annotations

import os
import uuid

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.api.deps import get_session_dependency
from app.main import app
from app.services.review import ReviewService


def test_create_case_review_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()

    async def fake_create_for_case(self, case_id, payload):
        return {
            "id": str(uuid.uuid4()),
            "case_id": str(case_id),
            "review_type": payload.review_type,
            "reviewer_reference": payload.reviewer_reference,
            "decision": payload.decision,
            "notes": payload.notes,
            "reviewed_at": "2026-04-02T00:00:00Z",
            "created_at": "2026-04-02T00:00:00Z",
            "updated_at": "2026-04-02T00:00:00Z",
        }

    monkeypatch.setattr(ReviewService, "create_for_case", fake_create_for_case)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/cases/{case_id}/reviews",
            json={
                "review_type": "attorney",
                "reviewer_reference": "attorney-1",
                "decision": "approved",
                "notes": "Ready to file",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["decision"] == "approved"


def test_get_case_timeline_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()

    async def fake_get_case_timeline(self, case_id):
        return [
            {
                "event_type": "audit_log",
                "entity_type": "document",
                "entity_id": str(uuid.uuid4()),
                "action": "document_uploaded",
                "actor_reference": "user-1",
                "occurred_at": "2026-04-02T12:00:00Z",
                "payload": {"case_id": str(case_id)},
            },
            {
                "event_type": "review",
                "entity_type": "review",
                "entity_id": str(uuid.uuid4()),
                "action": "review_approved",
                "actor_reference": "attorney-1",
                "occurred_at": "2026-04-02T10:00:00Z",
                "payload": {"review_type": "attorney", "decision": "approved"},
            },
        ]

    monkeypatch.setattr(ReviewService, "get_case_timeline", fake_get_case_timeline)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.get(f"/api/v1/cases/{case_id}/timeline")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["event_type"] == "audit_log"
