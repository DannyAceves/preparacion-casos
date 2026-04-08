from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.case_submission import CaseSubmission
from app.repositories.audit_log import AuditLogRepository
from app.repositories.case import CaseRepository
from app.repositories.case_submission import CaseSubmissionRepository
from app.schemas.case_readiness import CaseTransitionRequest
from app.schemas.case_submission import (
    CaseCloseRequest,
    CaseSubmissionApproveRequest,
    CaseSubmissionFailRequest,
    CaseSubmissionRead,
    CaseSubmissionSubmitRequest,
)
from app.services.case_readiness import CaseReadinessService


class CaseSubmissionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.case_repository = CaseRepository(session)
        self.submission_repository = CaseSubmissionRepository(session)
        self.audit_log_repository = AuditLogRepository(session)

    async def get_for_case(self, case_id: uuid.UUID) -> CaseSubmission:
        await self._get_case(case_id)
        submission = await self.submission_repository.get_for_case(case_id)
        if submission is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case submission not found")
        return submission

    async def approve_for_submission(
        self,
        case_id: uuid.UUID,
        payload: CaseSubmissionApproveRequest,
    ) -> CaseSubmission:
        await CaseReadinessService(self.session).transition_case(
            case_id,
            CaseTransitionRequest(
                target_status="ready_for_submission",
                actor_reference=payload.approved_by_user_id,
                notes=payload.notes,
            ),
        )
        submission = await self._get_or_create_submission(case_id)
        updated = await self.submission_repository.update(
            submission,
            {
                "status": "approved_for_submission",
                "approved_for_submission_at": datetime.now(UTC),
                "approved_by_user_id": payload.approved_by_user_id,
            },
        )
        await self._create_audit_log(
            case_id=case_id,
            entity_id=updated.id,
            action="case_submission_approved",
            actor_reference=payload.approved_by_user_id,
            payload={"notes": payload.notes},
        )
        await self.session.commit()
        return updated

    async def submit(
        self,
        case_id: uuid.UUID,
        payload: CaseSubmissionSubmitRequest,
    ) -> CaseSubmission:
        submission = await self._get_or_create_submission(case_id)
        if submission.status != "approved_for_submission":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="case submission must be approved before submit",
            )
        await CaseReadinessService(self.session).transition_case(
            case_id,
            CaseTransitionRequest(
                target_status="submitted",
                actor_reference=payload.submitted_by_user_id,
                notes=payload.notes,
            ),
        )
        updated = await self.submission_repository.update(
            submission,
            {
                "status": "submitted",
                "submitted_at": datetime.now(UTC),
                "submitted_by_user_id": payload.submitted_by_user_id,
                "submission_reference": payload.submission_reference,
                "failed_at": None,
                "failed_by_user_id": None,
                "failure_reason": None,
            },
        )
        await self._create_audit_log(
            case_id=case_id,
            entity_id=updated.id,
            action="case_submitted",
            actor_reference=payload.submitted_by_user_id,
            payload={
                "submission_reference": payload.submission_reference,
                "notes": payload.notes,
            },
        )
        await self.session.commit()
        return updated

    async def fail(
        self,
        case_id: uuid.UUID,
        payload: CaseSubmissionFailRequest,
    ) -> CaseSubmission:
        await self._get_case(case_id)
        submission = await self._get_or_create_submission(case_id)
        updated = await self.submission_repository.update(
            submission,
            {
                "status": "failed",
                "failed_at": datetime.now(UTC),
                "failed_by_user_id": payload.failed_by_user_id,
                "failure_reason": payload.failure_reason,
            },
        )
        await self._create_audit_log(
            case_id=case_id,
            entity_id=updated.id,
            action="case_submission_failed",
            actor_reference=payload.failed_by_user_id,
            payload={"failure_reason": payload.failure_reason},
        )
        await self.session.commit()
        return updated

    async def close_case(
        self,
        case_id: uuid.UUID,
        payload: CaseCloseRequest,
    ) -> Case:
        case = await self._get_case(case_id)
        submission = await self.submission_repository.get_for_case(case_id)
        if case.status != "submitted" and (submission is None or submission.status not in {"submitted", "failed"}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="case can only be closed after submitted or failed submission",
            )

        updated_case = await self.case_repository.update(case, {"status": "closed"})
        await self._create_audit_log(
            case_id=case_id,
            entity_id=updated_case.id,
            action="case_closed",
            actor_reference=payload.closed_by_user_id,
            payload={"notes": payload.notes},
        )
        await self.session.commit()
        return updated_case

    async def _get_or_create_submission(self, case_id: uuid.UUID) -> CaseSubmission:
        await self._get_case(case_id)
        submission = await self.submission_repository.get_for_case(case_id)
        if submission is not None:
            return submission
        return await self.submission_repository.create(
            {
                "case_id": case_id,
                "status": "draft",
                "approved_for_submission_at": None,
                "approved_by_user_id": None,
                "submitted_at": None,
                "submitted_by_user_id": None,
                "submission_reference": None,
                "failed_at": None,
                "failed_by_user_id": None,
                "failure_reason": None,
            }
        )

    async def _get_case(self, case_id: uuid.UUID) -> Case:
        case = await self.case_repository.get(case_id)
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
        return case

    async def _create_audit_log(
        self,
        *,
        case_id: uuid.UUID,
        entity_id: uuid.UUID,
        action: str,
        actor_reference: str | None,
        payload: dict[str, Any],
    ) -> AuditLog:
        return await self.audit_log_repository.create(
            {
                "case_id": case_id,
                "entity_type": "case_submission",
                "entity_id": str(entity_id),
                "action": action,
                "actor_reference": actor_reference,
                "payload": payload,
                "occurred_at": datetime.now(UTC),
            }
        )
