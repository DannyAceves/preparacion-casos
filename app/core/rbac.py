from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthenticatedPrincipal, SystemRole
from app.models.case import Case
from app.models.client import Client
from app.models.consultation import Consultation
from app.models.document import Document
from app.models.generated_form import GeneratedForm
from app.models.participant import Participant


class Permission(StrEnum):
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM_CONFIGURATION = "manage_system_configuration"
    MANAGE_INTAKE = "manage_intake"
    CONVERT_CONSULTATION = "convert_consultation"
    VIEW_CLIENTS = "view_clients"
    MANAGE_CLIENTS = "manage_clients"
    VIEW_CASES = "view_cases"
    MANAGE_CASES = "manage_cases"
    MANAGE_CASE_ASSIGNMENTS = "manage_case_assignments"
    MANAGE_DOCUMENT_CHECKLIST = "manage_document_checklist"
    VIEW_DOCUMENTS = "view_documents"
    MANAGE_DOCUMENTS = "manage_documents"
    REVIEW_DOCUMENT_EXTRACTION = "review_document_extraction"
    VIEW_CANONICAL_FIELDS = "view_canonical_fields"
    MANAGE_CANONICAL_FIELDS = "manage_canonical_fields"
    VIEW_INCONSISTENCIES = "view_inconsistencies"
    RESOLVE_INCONSISTENCIES = "resolve_inconsistencies"
    VIEW_QUESTIONNAIRES = "view_questionnaires"
    MANAGE_QUESTIONNAIRES = "manage_questionnaires"
    MANAGE_FORMS = "manage_forms"
    APPROVE_FORMS = "approve_forms"
    MANAGE_PACKETS = "manage_packets"
    VIEW_READINESS = "view_readiness"
    APPROVE_READINESS = "approve_readiness"
    VIEW_SUBMISSIONS = "view_submissions"
    APPROVE_SUBMISSIONS = "approve_submissions"
    EXECUTE_SUBMISSIONS = "execute_submissions"
    CREATE_REVIEWS = "create_reviews"
    VIEW_REVIEWS = "view_reviews"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    ISSUE_CLIENT_PORTAL_ACCESS = "issue_client_portal_access"
    MANAGE_TEMPLATES = "manage_templates"


ROLE_PERMISSIONS: dict[SystemRole, frozenset[Permission]] = {
    SystemRole.ADMIN: frozenset(permission for permission in Permission),
    SystemRole.RECEPTION: frozenset(
        {
            Permission.MANAGE_INTAKE,
            Permission.VIEW_CLIENTS,
            Permission.MANAGE_CLIENTS,
        }
    ),
    SystemRole.ATTORNEY: frozenset(
        {
            Permission.CONVERT_CONSULTATION,
            Permission.VIEW_CLIENTS,
            Permission.MANAGE_CLIENTS,
            Permission.VIEW_CASES,
            Permission.MANAGE_CASES,
            Permission.MANAGE_DOCUMENT_CHECKLIST,
            Permission.VIEW_DOCUMENTS,
            Permission.MANAGE_DOCUMENTS,
            Permission.REVIEW_DOCUMENT_EXTRACTION,
            Permission.VIEW_CANONICAL_FIELDS,
            Permission.MANAGE_CANONICAL_FIELDS,
            Permission.VIEW_INCONSISTENCIES,
            Permission.RESOLVE_INCONSISTENCIES,
            Permission.VIEW_QUESTIONNAIRES,
            Permission.MANAGE_QUESTIONNAIRES,
            Permission.MANAGE_FORMS,
            Permission.APPROVE_FORMS,
            Permission.MANAGE_PACKETS,
            Permission.VIEW_READINESS,
            Permission.APPROVE_READINESS,
            Permission.VIEW_SUBMISSIONS,
            Permission.APPROVE_SUBMISSIONS,
            Permission.EXECUTE_SUBMISSIONS,
            Permission.CREATE_REVIEWS,
            Permission.VIEW_REVIEWS,
            Permission.ISSUE_CLIENT_PORTAL_ACCESS,
        }
    ),
    SystemRole.PARALEGAL: frozenset(
        {
            Permission.CONVERT_CONSULTATION,
            Permission.VIEW_CLIENTS,
            Permission.MANAGE_CLIENTS,
            Permission.VIEW_CASES,
            Permission.MANAGE_CASES,
            Permission.MANAGE_DOCUMENT_CHECKLIST,
            Permission.VIEW_DOCUMENTS,
            Permission.MANAGE_DOCUMENTS,
            Permission.REVIEW_DOCUMENT_EXTRACTION,
            Permission.VIEW_CANONICAL_FIELDS,
            Permission.MANAGE_CANONICAL_FIELDS,
            Permission.VIEW_INCONSISTENCIES,
            Permission.VIEW_QUESTIONNAIRES,
            Permission.MANAGE_QUESTIONNAIRES,
            Permission.MANAGE_FORMS,
            Permission.MANAGE_PACKETS,
            Permission.VIEW_READINESS,
            Permission.VIEW_SUBMISSIONS,
            Permission.EXECUTE_SUBMISSIONS,
            Permission.VIEW_REVIEWS,
            Permission.ISSUE_CLIENT_PORTAL_ACCESS,
        }
    ),
    SystemRole.CLIENT: frozenset(),
}


def principal_has_permission(principal: AuthenticatedPrincipal, permission: Permission) -> bool:
    return any(permission in ROLE_PERMISSIONS.get(role, frozenset()) for role in principal.roles)


def require_permissions(principal: AuthenticatedPrincipal, *permissions: Permission) -> None:
    missing = [permission for permission in permissions if not principal_has_permission(principal, permission)]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="insufficient permissions",
        )


@dataclass(slots=True)
class AuthorizationService:
    session: AsyncSession

    async def authorize_case_access(
        self,
        principal: AuthenticatedPrincipal,
        case_id: uuid.UUID,
    ) -> Case:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")

        if principal.has_role(SystemRole.ADMIN):
            return case

        if principal.has_role(SystemRole.CLIENT):
            if principal.client_id is None or case.client_id != principal.client_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="case access denied")
            return case

        if principal.has_role(SystemRole.ATTORNEY, SystemRole.PARALEGAL):
            if principal.assigned_case_ids and case.id not in principal.assigned_case_ids:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="case is not assigned")
            return case

        return case

    async def authorize_consultation_access(
        self,
        principal: AuthenticatedPrincipal,
        consultation_id: uuid.UUID,
    ) -> Consultation:
        consultation = await self.session.get(Consultation, consultation_id)
        if consultation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="consultation not found")

        if principal.has_role(SystemRole.ADMIN, SystemRole.RECEPTION, SystemRole.PARALEGAL):
            return consultation

        if principal.has_role(SystemRole.ATTORNEY):
            if consultation.assigned_attorney and consultation.assigned_attorney != principal.subject:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="consultation is assigned to another attorney",
                )
            return consultation

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="consultation access denied")

    async def authorize_client_access(
        self,
        principal: AuthenticatedPrincipal,
        client_id: uuid.UUID,
    ) -> Client:
        client = await self.session.get(Client, client_id)
        if client is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="client not found")

        if principal.has_role(SystemRole.ADMIN):
            return client

        if principal.has_role(SystemRole.CLIENT):
            if principal.client_id != client.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="client access denied")
            return client

        return client

    async def authorize_document_access(
        self,
        principal: AuthenticatedPrincipal,
        document_id: uuid.UUID,
    ) -> Document:
        document = await self.session.get(Document, document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document not found")
        await self.authorize_case_access(principal, document.case_id)
        return document

    async def authorize_generated_form_access(
        self,
        principal: AuthenticatedPrincipal,
        generated_form_id: uuid.UUID,
    ) -> GeneratedForm:
        generated_form = await self.session.get(GeneratedForm, generated_form_id)
        if generated_form is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="generated form not found")
        await self.authorize_case_access(principal, generated_form.case_id)
        return generated_form

    async def authorize_participant_access(
        self,
        principal: AuthenticatedPrincipal,
        participant_id: uuid.UUID,
    ) -> Participant:
        participant = await self.session.get(Participant, participant_id)
        if participant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="participant not found")
        await self.authorize_case_access(principal, participant.case_id)
        return participant
