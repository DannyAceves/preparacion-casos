from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.api.deps import get_session_dependency
from app.core.auth import AuthenticatedPrincipal, SystemRole, get_current_principal
from app.main import app
from app.models.case import Case
from app.services.case_submission import CaseSubmissionService
from app.services.questionnaire_template_builder import QuestionnaireTemplateBuilderService
from app.services.system_user import SystemUserService


class FakeSession:
    def __init__(self, case_id: uuid.UUID | None = None, client_id: uuid.UUID | None = None) -> None:
        self.case_id = case_id
        self.client_id = client_id

    async def get(self, model, entity_id):
        if model is Case and self.case_id == entity_id:
            return SimpleNamespace(id=self.case_id, client_id=self.client_id)
        return None


def test_attorney_cannot_create_questionnaire_template(monkeypatch) -> None:
    async def fake_create_template(self, payload):
        return {
            "id": str(uuid.uuid4()),
            "case_type": payload.case_type,
            "title": payload.title,
            "description": None,
            "status": "draft",
            "version": 1,
            "is_active": False,
            "sections": [],
            "created_at": "2026-04-04T00:00:00Z",
            "updated_at": "2026-04-04T00:00:00Z",
        }

    monkeypatch.setattr(QuestionnaireTemplateBuilderService, "create_template", fake_create_template)

    async def fake_session_dependency():
        yield FakeSession()

    async def attorney_principal() -> AuthenticatedPrincipal:
        return AuthenticatedPrincipal(subject="attorney-1", roles=frozenset({SystemRole.ATTORNEY}))

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    app.dependency_overrides[get_current_principal] = attorney_principal
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/questionnaire-templates",
            json={
                "case_type": "family-based",
                "title": "I-751 Intake",
                "description": None,
                "status": "draft",
                "version": 1,
                "sections": [],
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "insufficient permissions"


def test_paralegal_cannot_approve_submission(monkeypatch) -> None:
    case_id = uuid.uuid4()
    client_id = uuid.uuid4()

    async def fake_approve(self, incoming_case_id, payload):
        assert incoming_case_id == case_id
        return {
            "id": str(uuid.uuid4()),
            "case_id": str(case_id),
            "status": "approved_for_submission",
            "approved_for_submission_at": "2026-04-04T00:00:00Z",
            "approved_by_user_id": payload.approved_by_user_id,
            "submitted_at": None,
            "submitted_by_user_id": None,
            "submission_reference": None,
            "failed_at": None,
            "failed_by_user_id": None,
            "failure_reason": None,
            "created_at": "2026-04-04T00:00:00Z",
            "updated_at": "2026-04-04T00:00:00Z",
        }

    monkeypatch.setattr(CaseSubmissionService, "approve_for_submission", fake_approve)

    async def fake_session_dependency():
        yield FakeSession(case_id=case_id, client_id=client_id)

    async def paralegal_principal() -> AuthenticatedPrincipal:
        return AuthenticatedPrincipal(subject="paralegal-1", roles=frozenset({SystemRole.PARALEGAL}))

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    app.dependency_overrides[get_current_principal] = paralegal_principal
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/cases/{case_id}/submission/approve",
            json={"approved_by_user_id": "attorney-1", "notes": "Ready to file"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "insufficient permissions"


def test_client_cannot_read_another_clients_case(monkeypatch) -> None:
    case_id = uuid.uuid4()
    owner_client_id = uuid.uuid4()
    other_client_id = uuid.uuid4()

    async def fake_session_dependency():
        yield FakeSession(case_id=case_id, client_id=owner_client_id)

    async def client_principal() -> AuthenticatedPrincipal:
        return AuthenticatedPrincipal(
            subject="client-1",
            roles=frozenset({SystemRole.CLIENT}),
            client_id=other_client_id,
        )

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    app.dependency_overrides[get_current_principal] = client_principal
    with TestClient(app) as client:
        response = client.get(f"/api/v1/cases/{case_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "case access denied"


def test_reception_cannot_list_system_users(monkeypatch) -> None:
    async def fake_session_dependency():
        yield FakeSession()

    async def reception_principal() -> AuthenticatedPrincipal:
        return AuthenticatedPrincipal(subject="reception-1", roles=frozenset({SystemRole.RECEPTION}))

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    app.dependency_overrides[get_current_principal] = reception_principal
    with TestClient(app) as client:
        response = client.get("/api/v1/admin/users")
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "insufficient permissions"


def test_admin_can_list_system_users(monkeypatch) -> None:
    now = datetime.now(timezone.utc)

    async def fake_list_filtered(self, filters):
        return [
            SimpleNamespace(
                id=uuid.uuid4(),
                first_name="Admin",
                last_name="User",
                email="admin@example.com",
                role="admin",
                is_active=True,
                last_login_at=None,
                created_at=now,
                updated_at=now,
            )
        ]

    monkeypatch.setattr(SystemUserService, "list_filtered", fake_list_filtered)

    async def fake_session_dependency():
        yield FakeSession()

    async def admin_principal() -> AuthenticatedPrincipal:
        return AuthenticatedPrincipal(subject="admin-1", roles=frozenset({SystemRole.ADMIN}))

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    app.dependency_overrides[get_current_principal] = admin_principal
    with TestClient(app) as client:
        response = client.get("/api/v1/admin/users?search=admin")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["email"] == "admin@example.com"
    assert payload[0]["role"] == "admin"


def test_email_login_returns_active_user_session(monkeypatch) -> None:
    user_id = uuid.uuid4()

    async def fake_authenticate(self, email):
        assert email == "admin@example.com"
        return SimpleNamespace(
            id=user_id,
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            role=SystemRole.ADMIN,
            is_active=True,
        )

    monkeypatch.setattr(SystemUserService, "authenticate_by_email", fake_authenticate)

    async def fake_session_dependency():
        yield FakeSession()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/login", json={"email": "admin@example.com"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(user_id)
    assert payload["email"] == "admin@example.com"
    assert payload["full_name"] == "Admin User"
    assert payload["role"] == "admin"
    assert payload["is_active"] is True


def test_email_login_rejects_unknown_or_inactive_user(monkeypatch) -> None:
    async def fake_session_dependency():
        yield FakeSession()

    from fastapi import HTTPException

    async def fake_authenticate_failure(self, email):
        raise HTTPException(status_code=401, detail="No active user found for this email.")

    monkeypatch.setattr(SystemUserService, "authenticate_by_email", fake_authenticate_failure)

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/login", json={"email": "missing@example.com"})
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "No active user found for this email."
