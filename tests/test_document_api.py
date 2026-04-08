from __future__ import annotations

import os
import uuid

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.api.deps import get_session_dependency
from app.main import app
from app.services.document_management import DocumentManagementService


def test_list_case_documents_endpoint(monkeypatch) -> None:
    case_id = uuid.uuid4()

    async def fake_list_case_documents(self, incoming_case_id):
        assert incoming_case_id == case_id
        return [
            {
                "id": str(uuid.uuid4()),
                "case_id": str(case_id),
                "uploaded_by_user_id": "user-1",
                "document_type": "passport",
                "original_filename": "passport.pdf",
                "stored_filename": "passport-v1.pdf",
                "storage_backend": "local",
                "storage_key": f"{case_id}/passport-v1.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 128,
                "sha256_hash": "0" * 64,
                "document_status": "uploaded",
                "processing_status": "uploaded",
                "classification_label": "passport",
                "classification_source": "manual",
                "file_metadata": {"size_bytes": 128},
                "extracted_metadata": None,
                "version_number": 1,
                "is_current": True,
                "previous_version_id": None,
                "root_document_id": str(uuid.uuid4()),
                "replacement_notes": None,
                "uploaded_at": "2026-04-02T00:00:00Z",
                "created_at": "2026-04-02T00:00:00Z",
                "updated_at": "2026-04-02T00:00:00Z",
            }
        ]

    monkeypatch.setattr(DocumentManagementService, "list_case_documents", fake_list_case_documents)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.get(f"/api/v1/cases/{case_id}/documents")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["case_id"] == str(case_id)


def test_get_document_detail_endpoint(monkeypatch) -> None:
    document_id = uuid.uuid4()
    root_document_id = uuid.uuid4()

    async def fake_get_document_detail(self, incoming_document_id):
        assert incoming_document_id == document_id
        return {
            "id": str(document_id),
            "case_id": str(uuid.uuid4()),
            "uploaded_by_user_id": "user-1",
            "document_type": "passport",
            "original_filename": "passport.pdf",
            "stored_filename": "passport-v2.pdf",
            "storage_backend": "local",
            "storage_key": "case/passport-v2.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 256,
            "sha256_hash": "1" * 64,
            "document_status": "uploaded",
            "processing_status": "uploaded",
            "classification_label": "passport",
            "classification_source": "manual",
            "file_metadata": {"size_bytes": 256},
            "extracted_metadata": None,
            "version_number": 2,
            "is_current": True,
            "previous_version_id": str(uuid.uuid4()),
            "root_document_id": str(root_document_id),
            "replacement_notes": "higher quality scan",
            "uploaded_at": "2026-04-02T00:00:00Z",
            "created_at": "2026-04-02T00:00:00Z",
            "updated_at": "2026-04-02T00:00:00Z",
            "versions": [
                {
                    "id": str(root_document_id),
                    "case_id": str(uuid.uuid4()),
                    "version_number": 1,
                    "is_current": False,
                    "original_filename": "passport.pdf",
                    "stored_filename": "passport-v1.pdf",
                    "document_status": "uploaded",
                    "classification_label": "passport",
                    "uploaded_at": "2026-04-01T00:00:00Z",
                    "created_at": "2026-04-01T00:00:00Z",
                    "updated_at": "2026-04-01T00:00:00Z",
                }
            ],
        }

    monkeypatch.setattr(DocumentManagementService, "get_document_detail", fake_get_document_detail)

    async def fake_session_dependency():
        yield object()

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    with TestClient(app) as client:
        response = client.get(f"/api/v1/documents/{document_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(document_id)
    assert response.json()["versions"][0]["version_number"] == 1
