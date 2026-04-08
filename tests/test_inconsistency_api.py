from __future__ import annotations

import os
import uuid

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.api.deps import get_session_dependency
from app.main import app
from app.services.inconsistency import InconsistencyService


def test_list_case_inconsistencies_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()

    async def fake_list_for_case(self, incoming_case_id):
        assert incoming_case_id == case_id
        return [
            {
                "id": str(uuid.uuid4()),
                "case_id": str(case_id),
                "field_key": "beneficiary.date_of_birth",
                "severity": "high",
                "status": "open",
                "description": "Mismatch between sources",
                "evidence_payload": {"sources": ["passport", "questionnaire"]},
                "resolution_notes": None,
                "resolved_by_user_id": None,
                "resolved_at": None,
                "created_at": "2026-04-02T00:00:00Z",
                "updated_at": "2026-04-02T00:00:00Z",
            }
        ]

    monkeypatch.setattr(InconsistencyService, "list_for_case", fake_list_for_case)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.get(f"/api/v1/cases/{case_id}/inconsistencies")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["severity"] == "high"


def test_resolve_inconsistency_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()
    inconsistency_id = uuid.uuid4()

    async def fake_resolve_for_case(self, case_id, inconsistency_id, payload):
        return {
            "id": str(inconsistency_id),
            "case_id": str(case_id),
            "field_key": "beneficiary.date_of_birth",
            "severity": "high",
            "status": "resolved",
            "description": "Mismatch between sources",
            "evidence_payload": {"sources": ["passport", "questionnaire"]},
            "resolution_notes": payload.notes,
            "resolved_by_user_id": payload.actor_reference,
            "resolved_at": "2026-04-02T00:00:00Z",
            "created_at": "2026-04-02T00:00:00Z",
            "updated_at": "2026-04-02T00:00:00Z",
        }

    monkeypatch.setattr(InconsistencyService, "resolve_for_case", fake_resolve_for_case)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/cases/{case_id}/inconsistencies/{inconsistency_id}/resolve",
            json={"actor_reference": "lawyer-1", "notes": "Verified passport"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"
