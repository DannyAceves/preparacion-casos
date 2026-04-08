from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum

from fastapi import Header, HTTPException, Request, status


class SystemRole(StrEnum):
    ADMIN = "admin"
    RECEPTION = "reception"
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    CLIENT = "client"


class PrincipalSource(StrEnum):
    HEADERS = "headers"
    KEYCLOAK = "keycloak"
    CLIENT_PORTAL = "client_portal"


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    subject: str
    roles: frozenset[SystemRole]
    source: PrincipalSource = PrincipalSource.HEADERS
    client_id: uuid.UUID | None = None
    email: str | None = None
    assigned_case_ids: frozenset[uuid.UUID] = field(default_factory=frozenset)

    def has_role(self, *roles: SystemRole) -> bool:
        return any(role in self.roles for role in roles)


def _parse_roles(raw_roles: str | None) -> frozenset[SystemRole]:
    if raw_roles is None or not raw_roles.strip():
        return frozenset()
    roles: set[SystemRole] = set()
    for item in raw_roles.split(","):
        normalized = item.strip().lower()
        if not normalized:
            continue
        try:
            roles.add(SystemRole(normalized))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"unsupported role '{normalized}'",
            ) from exc
    return frozenset(roles)


def _parse_uuid_set(raw_value: str | None, *, field_name: str) -> frozenset[uuid.UUID]:
    if raw_value is None or not raw_value.strip():
        return frozenset()
    values: set[uuid.UUID] = set()
    for item in raw_value.split(","):
        normalized = item.strip()
        if not normalized:
            continue
        try:
            values.add(uuid.UUID(normalized))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"invalid UUID in {field_name}",
            ) from exc
    return frozenset(values)


def _parse_uuid_value(raw_value: str | None, *, field_name: str) -> uuid.UUID | None:
    if raw_value is None or not raw_value.strip():
        return None
    try:
        return uuid.UUID(raw_value.strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid UUID in {field_name}",
        ) from exc


def _normalize_principal(candidate: object) -> AuthenticatedPrincipal | None:
    if isinstance(candidate, AuthenticatedPrincipal):
        return candidate
    if isinstance(candidate, dict):
        subject = str(candidate.get("subject", "")).strip()
        if not subject:
            return None
        raw_roles = candidate.get("roles", [])
        if isinstance(raw_roles, str):
            parsed_roles = _parse_roles(raw_roles)
        else:
            parsed_roles = _parse_roles(",".join(str(role) for role in raw_roles))
        assigned_case_ids = candidate.get("assigned_case_ids", [])
        if isinstance(assigned_case_ids, str):
            parsed_case_ids = _parse_uuid_set(
                assigned_case_ids,
                field_name="assigned_case_ids",
            )
        else:
            parsed_case_ids = frozenset(
                uuid.UUID(str(case_id)) for case_id in assigned_case_ids if str(case_id).strip()
            )
        client_id = candidate.get("client_id")
        raw_source = candidate.get("source", PrincipalSource.KEYCLOAK)
        source = raw_source if isinstance(raw_source, PrincipalSource) else PrincipalSource(str(raw_source))
        return AuthenticatedPrincipal(
            subject=subject,
            roles=parsed_roles,
            source=source,
            client_id=uuid.UUID(str(client_id)) if client_id else None,
            email=str(candidate.get("email")) if candidate.get("email") else None,
            assigned_case_ids=parsed_case_ids,
        )
    return None


async def get_current_principal(
    request: Request,
    x_principal_subject: str | None = Header(default=None, alias="X-Principal-Subject"),
    x_principal_roles: str | None = Header(default=None, alias="X-Principal-Roles"),
    x_principal_client_id: str | None = Header(default=None, alias="X-Principal-Client-Id"),
    x_principal_email: str | None = Header(default=None, alias="X-Principal-Email"),
    x_principal_case_ids: str | None = Header(default=None, alias="X-Principal-Case-Ids"),
) -> AuthenticatedPrincipal:
    """
    Resolve the authenticated principal.

    Today the backend accepts lightweight identity headers so local development
    and tests can exercise RBAC without baking in a custom login flow. A future
    Keycloak middleware can place a normalized principal in `request.state`.
    """

    state_principal = _normalize_principal(getattr(request.state, "authenticated_principal", None))
    if state_principal is not None:
        return state_principal

    subject = (x_principal_subject or "").strip()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing authenticated principal",
        )

    roles = _parse_roles(x_principal_roles)
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing principal roles",
        )

    return AuthenticatedPrincipal(
        subject=subject,
        roles=roles,
        source=PrincipalSource.HEADERS,
        client_id=_parse_uuid_value(x_principal_client_id, field_name="X-Principal-Client-Id"),
        email=(x_principal_email or None),
        assigned_case_ids=_parse_uuid_set(x_principal_case_ids, field_name="X-Principal-Case-Ids"),
    )
