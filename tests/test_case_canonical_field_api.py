from __future__ import annotations

import os
import uuid

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.api.deps import get_session_dependency
from app.main import app
from app.services.case_canonical_field import CaseCanonicalFieldService


def test_list_case_canonical_fields_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()

    async def fake_list_for_case(self, incoming_case_id):
        assert incoming_case_id == case_id
        return [
            {
                "id": str(uuid.uuid4()),
                "case_id": str(case_id),
                "source_document_id": None,
                "field_key": "beneficiary.full_name",
                "field_value": "Demo Applicant",
                "confidence_score": "0.98",
                "source_priority": 100,
                "status": "approved",
                "created_at": "2026-04-02T00:00:00Z",
                "updated_at": "2026-04-02T00:00:00Z",
            }
        ]

    monkeypatch.setattr(CaseCanonicalFieldService, "list_for_case", fake_list_for_case)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.get(f"/api/v1/cases/{case_id}/canonical-fields")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["field_key"] == "beneficiary.full_name"


def test_patch_case_canonical_field_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()

    async def fake_upsert_by_field_key(self, *, case_id: uuid.UUID, field_key: str, payload):
        assert field_key == "beneficiary.full_name"
        return {
            "id": str(uuid.uuid4()),
            "case_id": str(case_id),
            "source_document_id": None,
            "field_key": field_key,
            "field_value": payload.field_value,
            "confidence_score": "0.90",
            "source_priority": 90,
            "status": payload.status,
            "created_at": "2026-04-02T00:00:00Z",
            "updated_at": "2026-04-02T00:00:00Z",
        }

    monkeypatch.setattr(CaseCanonicalFieldService, "upsert_by_field_key", fake_upsert_by_field_key)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.patch(
            f"/api/v1/cases/{case_id}/canonical-fields/beneficiary.full_name",
            json={
                "actor_reference": "lawyer-1",
                "field_value": "Demo Applicant",
                "source_priority": 90,
                "status": "approved",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
