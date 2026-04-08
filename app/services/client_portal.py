from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.client_portal import ClientPortalAccess
from app.models.audit_log import AuditLog
from app.repositories.client_portal import ClientPortalAccessRepository
from app.repositories.audit_log import AuditLogRepository
from app.schemas.case_questionnaire import (
    CaseQuestionnaireAnswerUpdateRequest,
    CaseQuestionnaireAnswersUpsertRequest,
    CaseQuestionnaireAnswerUpsert,
    QuestionnaireAnswerPayload,
    QuestionnaireAnswerRead,
)
from app.schemas.client_portal import (
    ClientPortalAccessRead,
    ClientPortalContextRead,
    ClientPortalDocumentUploadResponse,
    ClientPortalIssuedRead,
    ClientPortalIssueRequest,
    ClientPortalProgressRead,
    ClientPortalSessionRead,
)
from app.schemas.document_checklist import CaseDocumentChecklistItemUpdate
from app.services.case_questionnaire import CaseQuestionnaireService
from app.services.document_checklist import DocumentChecklistService
from app.services.document_management import DocumentManagementService

PORTAL_SESSION_TTL_HOURS = 12
PORTAL_MAX_FAILED_ATTEMPTS = 5
PORTAL_LOCK_MINUTES = 15


class ClientPortalService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.portal_repository = ClientPortalAccessRepository(session)
        self.audit_log_repository = AuditLogRepository(session)

    async def get_case_portal_access(self, case_id: uuid.UUID) -> ClientPortalAccessRead | None:
        portal = await self.portal_repository.get_for_case(case_id)
        if portal is None:
            return None
        return self._serialize_access(portal)

    async def issue_case_portal_access(
        self,
        case_id: uuid.UUID,
        payload: ClientPortalIssueRequest,
    ) -> ClientPortalIssuedRead:
        case = await self._get_case(case_id)
        token = secrets.token_urlsafe(24)
        passcode = secrets.token_hex(3).upper()
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=payload.expires_in_days)
        token_hash = self._hash_value(token)
        passcode_hash = self._hash_value(passcode)
        instructions = payload.instructions if payload.instructions is not None else case.summary

        existing = await self.portal_repository.get_for_case(case.id)
        if existing is None:
            portal = await self.portal_repository.create(
                {
                    "case_id": case.id,
                    "token_hash": token_hash,
                    "token_last4": token[-4:],
                    "passcode_hash": passcode_hash,
                    "instructions": instructions,
                    "expires_at": expires_at,
                    "is_active": True,
                    "last_accessed_at": None,
                    "access_session_hash": None,
                    "access_session_expires_at": None,
                    "failed_access_attempt_count": 0,
                    "last_failed_access_at": None,
                    "locked_until": None,
                }
            )
        else:
            portal = await self.portal_repository.update(
                existing,
                {
                    "token_hash": token_hash,
                    "token_last4": token[-4:],
                    "passcode_hash": passcode_hash,
                    "instructions": instructions,
                    "expires_at": expires_at,
                    "is_active": True,
                    "access_session_hash": None,
                    "access_session_expires_at": None,
                    "failed_access_attempt_count": 0,
                    "last_failed_access_at": None,
                    "locked_until": None,
                },
            )

        await self._create_audit_log(
            case_id=case.id,
            entity_type="client_portal_access",
            entity_id=portal.id,
            action="client_portal_access_issued",
            actor_reference="staff_portal_issue",
            payload={
                "expires_at": expires_at.isoformat(),
                "token_last4": token[-4:],
                "is_regenerated": existing is not None,
            },
        )
        await self.session.commit()

        return ClientPortalIssuedRead(
            **self._serialize_access(portal).model_dump(),
            token=token,
            passcode=passcode,
            portal_path=f"/portal/{token}",
        )

    async def authenticate_portal(self, token: str, passcode: str) -> ClientPortalSessionRead:
        portal = await self._authenticate_with_credentials(token, passcode)
        session_token, session_expires_at = await self._issue_session_token(portal)
        await self.session.commit()
        return ClientPortalSessionRead(
            session_token=session_token,
            session_expires_at=session_expires_at,
        )

    async def get_portal_context(
        self,
        token: str | None = None,
        passcode: str | None = None,
        portal_session_token: str | None = None,
    ) -> ClientPortalContextRead:
        portal, session_token, session_expires_at = await self._authenticate(
            token=token,
            passcode=passcode,
            portal_session_token=portal_session_token,
        )
        case = await self._get_case(portal.case_id)

        questionnaire = await self._optional_questionnaire(case.id)
        checklist = await DocumentChecklistService(self.session).get_case_checklist(case.id)
        documents = await self._list_client_visible_documents(case.id)
        progress = self._build_progress(questionnaire, checklist)

        await self.portal_repository.update(
            portal,
            {
                "last_accessed_at": datetime.now(UTC),
                "failed_access_attempt_count": 0,
                "last_failed_access_at": None,
                "locked_until": None,
            },
        )
        await self._create_audit_log(
            case_id=case.id,
            entity_type="client_portal_access",
            entity_id=portal.id,
            action="client_portal_context_viewed",
            actor_reference=f"client-portal:{portal.id}",
            payload={"session_expires_at": session_expires_at.isoformat() if session_expires_at else None},
        )
        await self.session.commit()

        return ClientPortalContextRead(
            case_id=case.id,
            case_number=case.case_number,
            case_type=case.case_type,
            case_title=case.title,
            case_summary=case.summary,
            instructions=portal.instructions,
            access_expires_at=portal.expires_at,
            session_token=session_token,
            session_expires_at=session_expires_at,
            questionnaire=questionnaire,
            checklist=checklist,
            documents=documents,
            progress=progress,
        )

    async def save_answer(
        self,
        token: str | None,
        passcode: str | None,
        question_id: uuid.UUID,
        value: dict[str, Any],
        portal_session_token: str | None = None,
    ) -> QuestionnaireAnswerRead:
        portal, _, _ = await self._authenticate(
            token=token,
            passcode=passcode,
            portal_session_token=portal_session_token,
        )
        service = CaseQuestionnaireService(self.session)
        answers = await service.upsert_answers(
            portal.case_id,
            CaseQuestionnaireAnswersUpsertRequest(
                actor_reference="client_portal",
                answers=[
                    CaseQuestionnaireAnswerUpsert(
                        question_id=question_id,
                        value=QuestionnaireAnswerPayload.model_validate(value),
                    )
                ],
            ),
        )
        await self._create_audit_log(
            case_id=portal.case_id,
            entity_type="client_portal_access",
            entity_id=portal.id,
            action="client_portal_answer_saved",
            actor_reference=f"client-portal:{portal.id}",
            payload={"question_id": str(question_id)},
        )
        await self.session.commit()
        return QuestionnaireAnswerRead.model_validate(answers[0])

    async def update_answer(
        self,
        token: str | None,
        passcode: str | None,
        answer_id: uuid.UUID,
        payload: CaseQuestionnaireAnswerUpdateRequest,
        portal_session_token: str | None = None,
    ) -> QuestionnaireAnswerRead:
        portal, _, _ = await self._authenticate(
            token=token,
            passcode=passcode,
            portal_session_token=portal_session_token,
        )
        answer = await CaseQuestionnaireService(self.session).update_answer(
            portal.case_id,
            answer_id,
            CaseQuestionnaireAnswerUpdateRequest(
                actor_reference="client_portal",
                value=payload.value,
            ),
        )
        await self._create_audit_log(
            case_id=portal.case_id,
            entity_type="client_portal_access",
            entity_id=portal.id,
            action="client_portal_answer_updated",
            actor_reference=f"client-portal:{portal.id}",
            payload={"answer_id": str(answer_id)},
        )
        await self.session.commit()
        return QuestionnaireAnswerRead.model_validate(answer)

    async def upload_document(
        self,
        token: str | None,
        passcode: str | None,
        file: UploadFile,
        document_type: str | None = None,
        checklist_item_id: uuid.UUID | None = None,
        portal_session_token: str | None = None,
    ) -> ClientPortalDocumentUploadResponse:
        portal, _, _ = await self._authenticate(
            token=token,
            passcode=passcode,
            portal_session_token=portal_session_token,
        )
        document = await DocumentManagementService(self.session).upload_document(
            case_id=portal.case_id,
            uploaded_by_user_id=f"client-portal:{portal.id}",
            file=file,
            document_status="received_from_client",
            classification_label=document_type,
            classification_source="client_portal" if document_type else None,
        )

        checklist_service = DocumentChecklistService(self.session)
        checklist = await checklist_service.get_case_checklist(portal.case_id)

        updates: list[uuid.UUID] = []
        if checklist_item_id is not None:
            updates.append(checklist_item_id)
        elif document_type:
            updates.extend(
                item.id
                for item in checklist.items
                if item.document_type and item.document_type.lower() == document_type.lower()
            )

        for item_id in updates:
            checklist = await checklist_service.update_item(
                portal.case_id,
                item_id,
                CaseDocumentChecklistItemUpdate(
                    requested=True,
                    received=True,
                ),
            )

        await self._create_audit_log(
            case_id=portal.case_id,
            entity_type="client_portal_access",
            entity_id=portal.id,
            action="client_portal_document_uploaded",
            actor_reference=f"client-portal:{portal.id}",
            payload={
                "document_id": str(document.id),
                "checklist_item_id": str(checklist_item_id) if checklist_item_id else None,
                "document_type": document_type,
            },
        )
        await self.session.commit()

        return ClientPortalDocumentUploadResponse(document=document, checklist=checklist)

    async def _authenticate(
        self,
        *,
        token: str | None,
        passcode: str | None,
        portal_session_token: str | None,
    ) -> tuple[ClientPortalAccess, str, datetime | None]:
        if portal_session_token:
            portal = await self._authenticate_with_session(portal_session_token)
            return portal, portal_session_token, portal.access_session_expires_at
        if not token or not passcode:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="portal credentials are required")
        portal = await self._authenticate_with_credentials(token, passcode)
        session_token, session_expires_at = await self._issue_session_token(portal)
        return portal, session_token, session_expires_at

    async def _authenticate_with_credentials(self, token: str, passcode: str) -> ClientPortalAccess:
        portal = await self.portal_repository.get_by_token_hash(self._hash_value(token))
        if portal is None or not portal.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="portal access not found")
        now = datetime.now(UTC)
        if portal.locked_until is not None and portal.locked_until > now:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="portal access is temporarily locked")
        if portal.expires_at is not None and portal.expires_at < datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="portal access has expired")
        if portal.passcode_hash != self._hash_value(passcode):
            attempts = portal.failed_access_attempt_count + 1
            lock_until = now + timedelta(minutes=PORTAL_LOCK_MINUTES) if attempts >= PORTAL_MAX_FAILED_ATTEMPTS else None
            await self.portal_repository.update(
                portal,
                {
                    "failed_access_attempt_count": attempts,
                    "last_failed_access_at": now,
                    "locked_until": lock_until,
                },
            )
            await self._create_audit_log(
                case_id=portal.case_id,
                entity_type="client_portal_access",
                entity_id=portal.id,
                action="client_portal_auth_failed",
                actor_reference=f"client-portal:{portal.id}",
                payload={"failed_access_attempt_count": attempts, "locked_until": lock_until.isoformat() if lock_until else None},
            )
            await self.session.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid portal credentials")
        await self.portal_repository.update(
            portal,
            {
                "failed_access_attempt_count": 0,
                "last_failed_access_at": None,
                "locked_until": None,
                "last_accessed_at": now,
            },
        )
        await self._create_audit_log(
            case_id=portal.case_id,
            entity_type="client_portal_access",
            entity_id=portal.id,
            action="client_portal_auth_succeeded",
            actor_reference=f"client-portal:{portal.id}",
            payload={"token_last4": portal.token_last4},
        )
        return portal

    async def _authenticate_with_session(self, portal_session_token: str) -> ClientPortalAccess:
        portal = await self.portal_repository.get_by_session_hash(self._hash_value(portal_session_token))
        if portal is None or not portal.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="portal session is invalid")
        now = datetime.now(UTC)
        if portal.expires_at is not None and portal.expires_at < now:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="portal access has expired")
        if portal.access_session_expires_at is None or portal.access_session_expires_at <= now:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="portal session has expired")
        return portal

    async def _get_case(self, case_id: uuid.UUID) -> Case:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
        return case

    async def _optional_questionnaire(self, case_id: uuid.UUID):
        try:
            return await CaseQuestionnaireService(self.session).get_case_questionnaire(case_id)
        except HTTPException as exc:
            if exc.status_code == status.HTTP_404_NOT_FOUND:
                return None
            raise

    def _build_progress(self, questionnaire, checklist) -> ClientPortalProgressRead:
        total_questions = 0
        answered_questions = 0
        if questionnaire is not None:
            total_questions = sum(len(section.questions) for section in questionnaire.sections)
            answered_questions = sum(
                1
                for section in questionnaire.sections
                for question in section.questions
                if question.answer is not None
            )
        questionnaire_percent = round((answered_questions / total_questions) * 100) if total_questions else 0
        checklist_percent = checklist.progress.percent_complete
        overall = round((questionnaire_percent + checklist_percent) / 2) if (total_questions or checklist.progress.applicable_items) else 0
        return ClientPortalProgressRead(
            questionnaire_total_questions=total_questions,
            questionnaire_answered_questions=answered_questions,
            questionnaire_percent_complete=questionnaire_percent,
            checklist_applicable_items=checklist.progress.applicable_items,
            checklist_received_items=checklist.progress.received_items,
            checklist_validated_items=checklist.progress.validated_items,
            checklist_percent_complete=checklist_percent,
            overall_percent_complete=overall,
        )

    async def _list_client_visible_documents(self, case_id: uuid.UUID) -> list[Any]:
        documents = await DocumentManagementService(self.session).list_case_documents(case_id)
        return [
            document
            for document in documents
            if document.uploaded_by_user_id.startswith("client-portal:")
            or document.document_status == "received_from_client"
        ]

    def _serialize_access(self, portal: ClientPortalAccess) -> ClientPortalAccessRead:
        return ClientPortalAccessRead(
            case_id=portal.case_id,
            token_last4=portal.token_last4,
            instructions=portal.instructions,
            expires_at=portal.expires_at,
            is_active=portal.is_active,
            last_accessed_at=portal.last_accessed_at,
            failed_access_attempt_count=portal.failed_access_attempt_count,
            last_failed_access_at=portal.last_failed_access_at,
            locked_until=portal.locked_until,
            access_session_expires_at=portal.access_session_expires_at,
        )

    def _hash_value(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    async def _issue_session_token(self, portal: ClientPortalAccess) -> tuple[str, datetime]:
        session_token = secrets.token_urlsafe(32)
        session_expires_at = datetime.now(UTC) + timedelta(hours=PORTAL_SESSION_TTL_HOURS)
        if portal.expires_at is not None and session_expires_at > portal.expires_at:
            session_expires_at = portal.expires_at
        await self.portal_repository.update(
            portal,
            {
                "access_session_hash": self._hash_value(session_token),
                "access_session_expires_at": session_expires_at,
            },
        )
        return session_token, session_expires_at

    async def _create_audit_log(
        self,
        *,
        case_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        actor_reference: str,
        payload: dict[str, Any],
    ) -> AuditLog:
        return await self.audit_log_repository.create(
            {
                "case_id": case_id,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "action": action,
                "actor_reference": actor_reference,
                "payload": payload,
                "occurred_at": datetime.now(UTC),
            }
        )
