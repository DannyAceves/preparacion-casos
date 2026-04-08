from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture(autouse=True)
def override_test_principal() -> None:
    from app.core.auth import AuthenticatedPrincipal, SystemRole, get_current_principal
    from app.main import app

    async def fake_principal() -> AuthenticatedPrincipal:
        return AuthenticatedPrincipal(
            subject="test-admin",
            roles=frozenset({SystemRole.ADMIN}),
        )

    app.dependency_overrides[get_current_principal] = fake_principal
    yield
    app.dependency_overrides.pop(get_current_principal, None)
