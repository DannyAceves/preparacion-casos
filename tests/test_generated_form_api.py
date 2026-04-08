from __future__ import annotations

import os
import uuid

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.api.deps import get_session_dependency
from app.main import app
from app.services.generated_form import GeneratedFormService


def test_generate_case_forms_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()
    generated_form_id = uuid.uuid4()
    form_id = uuid.uuid4()

    async def fake_generate_for_case(self, incoming_case_id, payload):
        assert incoming_case_id == case_id
        assert payload.generated_by_reference == "paralegal-1"
        return [
            {
                "id": str(generated_form_id),
                "case_id": str(case_id),
                "form_id": str(form_id),
                "draft_version": 1,
                "status": "draft",
                "generated_payload": {"form_code": "I-130", "fields": {}},
                "warnings_payload": [],
                "export_path": "/tmp/forms/CASE-001/I-130/draft-v1.json",
                "review_notes": None,
                "generated_at": "2026-04-02T00:00:00Z",
                "reviewed_by_user_id": None,
                "reviewed_at": None,
                "created_at": "2026-04-02T00:00:00Z",
                "updated_at": "2026-04-02T00:00:00Z",
            }
        ]

    monkeypatch.setattr(GeneratedFormService, "generate_for_case", fake_generate_for_case)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/cases/{case_id}/forms/generate",
            json={"generated_by_reference": "paralegal-1", "export_base_path": "/tmp/forms"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()[0]["id"] == str(generated_form_id)


def test_get_generated_form_detail_endpoint(monkeypatch) -> None:
    generated_form_id = uuid.uuid4()
    form_id = uuid.uuid4()

    async def fake_get_detail(self, incoming_generated_form_id):
        assert incoming_generated_form_id == generated_form_id
        return {
            "id": str(generated_form_id),
            "case_id": str(uuid.uuid4()),
            "form_id": str(form_id),
            "draft_version": 1,
            "status": "review_pending",
            "generated_payload": {"form_code": "I-130", "fields": {}},
            "warnings_payload": [{"type": "missing_required_field"}],
            "export_path": None,
            "review_notes": None,
            "generated_at": "2026-04-02T00:00:00Z",
            "reviewed_by_user_id": None,
            "reviewed_at": None,
            "created_at": "2026-04-02T00:00:00Z",
            "updated_at": "2026-04-02T00:00:00Z",
            "form": {
                "form_id": str(form_id),
                "form_code": "I-130",
                "form_name": "Petition",
                "version": 1,
                "case_type_id": "family-based",
            },
        }

    monkeypatch.setattr(GeneratedFormService, "get_detail", fake_get_detail)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.get(f"/api/v1/generated-forms/{generated_form_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["form"]["form_code"] == "I-130"
