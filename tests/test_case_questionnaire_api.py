from __future__ import annotations

import os
import uuid

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.api.deps import get_session_dependency
from app.main import app
from app.services.case_questionnaire import CaseQuestionnaireService


def test_get_case_questionnaire_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()

    async def fake_get_case_questionnaire(self, incoming_case_id):
        assert incoming_case_id == case_id
        return {
            "case_id": str(case_id),
            "case_type": "family-based",
            "questionnaire": {
                "id": str(uuid.uuid4()),
                "case_type": "family-based",
                "title": "Family-Based Intake Questionnaire",
                "description": None,
                "status": "active",
                "version": 1,
            },
            "sections": [],
        }

    monkeypatch.setattr(
        CaseQuestionnaireService,
        "get_case_questionnaire",
        fake_get_case_questionnaire,
    )

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.get(f"/api/v1/cases/{case_id}/questionnaire")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_id"] == str(case_id)
    assert payload["case_type"] == "family-based"
