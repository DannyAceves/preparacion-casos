from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.case import Case
from app.repositories.audit_log import AuditLogRepository
from app.repositories.case import CaseRepository
from app.repositories.document import DocumentRepository
from app.repositories.generated_form import GeneratedFormRepository
from app.repositories.inconsistency import InconsistencyRepository
from app.repositories.review import ReviewRepository
from app.schemas.case_readiness import (
    CaseReadinessIssueRead,
    CaseReadinessRead,
    CaseReadinessSummaryRead,
    CaseReadinessValidateRequest,
    CaseTargetReadinessRead,
    CaseTargetStatus,
    CaseTransitionRequest,
)

REQUIRED_DOCUMENTS_BY_CASE_TYPE: dict[str, list[str]] = {
    "family-based": ["passport", "birth_certificate", "marriage_certificate", "evidence"],
}


class CaseReadinessService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.case_repository = CaseRepository(session)
        self.document_repository = DocumentRepository(session)
        self.generated_form_repository = GeneratedFormRepository(session)
        self.inconsistency_repository = InconsistencyRepository(session)
        self.review_repository = ReviewRepository(session)
        self.audit_log_repository = AuditLogRepository(session)

    async def get_readiness(self, case_id: uuid.UUID) -> CaseReadinessRead:
        case = await self._get_case(case_id)
        documents = await self.document_repository.list_current_for_case(case_id)
        inconsistencies = await self.inconsistency_repository.list_for_case(case_id)
        generated_forms = await self.generated_form_repository.list_for_case(case_id)
        reviews = await self.review_repository.list_for_case(case_id)
        return self._build_readiness(case, documents, inconsistencies, generated_forms, reviews)

    async def validate_readiness(
        self,
        case_id: uuid.UUID,
        payload: CaseReadinessValidateRequest,
    ) -> CaseReadinessRead:
        readiness = await self.get_readiness(case_id)
        await self._create_audit_log(
            case_id=case_id,
            entity_id=case_id,
            action="case_readiness_validated",
            actor_reference=payload.actor_reference,
            payload={
                "case_status": readiness.case_status,
                "targets": [item.model_dump() for item in readiness.targets],
            },
        )
        await self.session.commit()
        return readiness

    async def transition_case(
        self,
        case_id: uuid.UUID,
        payload: CaseTransitionRequest,
    ) -> Case:
        case = await self._get_case(case_id)
        readiness = await self.get_readiness(case_id)
        target = next((item for item in readiness.targets if item.target_status == payload.target_status), None)
        if target is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported target status")
        if not target.is_ready:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": f"case cannot transition to '{payload.target_status}'",
                    "blockers": [item.model_dump() for item in target.blockers],
                },
            )

        previous_status = case.status
        updated = await self.case_repository.update(case, {"status": payload.target_status})
        await self._create_audit_log(
            case_id=case_id,
            entity_id=updated.id,
            action="case_status_transitioned",
            actor_reference=payload.actor_reference,
            payload={
                "from_status": previous_status,
                "to_status": payload.target_status,
                "notes": payload.notes,
            },
        )
        await self.session.commit()
        return updated

    def _build_readiness(
        self,
        case: Case,
        documents: list[object],
        inconsistencies: list[object],
        generated_forms: list[object],
        reviews: list[object],
    ) -> CaseReadinessRead:
        required_document_types = REQUIRED_DOCUMENTS_BY_CASE_TYPE.get(case.case_type, ["passport", "evidence"])
        valid_documents = [
            document
            for document in documents
            if document.document_status not in {"rejected", "archived"}
            and document.processing_status != "failed"
        ]
        present_required_document_types = sorted(
            {document.document_type for document in valid_documents if document.document_type in required_document_types}
        )
        missing_required_document_types = sorted(
            [document_type for document_type in required_document_types if document_type not in present_required_document_types]
        )

        open_high_or_critical_inconsistencies = [
            item
            for item in inconsistencies
            if item.status in {"open", "under_review"} and item.severity in {"high", "critical"}
        ]
        open_critical_inconsistencies = [
            item
            for item in inconsistencies
            if item.status in {"open", "under_review"} and item.severity == "critical"
        ]
        open_high_inconsistencies = [
            item
            for item in inconsistencies
            if item.status in {"open", "under_review"} and item.severity == "high"
        ]
        unapproved_generated_forms = [item for item in generated_forms if item.status != "approved"]
        attorney_approved_review_exists = any(
            review.review_type == "attorney" and review.decision == "approved"
            for review in reviews
        )

        summary = CaseReadinessSummaryRead(
            required_document_types=required_document_types,
            present_required_document_types=present_required_document_types,
            missing_required_document_types=missing_required_document_types,
            open_high_or_critical_inconsistency_count=len(open_high_or_critical_inconsistencies),
            open_critical_inconsistency_count=len(open_critical_inconsistencies),
            unapproved_generated_form_count=len(unapproved_generated_forms),
            generated_form_count=len(generated_forms),
            attorney_approved_review_exists=attorney_approved_review_exists,
        )

        attorney_review_blockers = self._build_document_blockers(missing_required_document_types)
        attorney_review_warnings = self._build_high_inconsistency_warnings(open_high_inconsistencies)
        if len(generated_forms) == 0:
            attorney_review_blockers.append(
                CaseReadinessIssueRead(
                    code="missing_generated_forms",
                    message="At least one generated form is required before attorney review.",
                    severity="blocking",
                )
            )

        ready_for_submission_blockers = self._build_document_blockers(missing_required_document_types)
        ready_for_submission_warnings = self._build_high_inconsistency_warnings(open_high_inconsistencies)
        if open_critical_inconsistencies:
            ready_for_submission_blockers.append(
                CaseReadinessIssueRead(
                    code="open_critical_inconsistencies",
                    message="Critical inconsistencies must be resolved before ready_for_submission.",
                    severity="blocking",
                )
            )
        if unapproved_generated_forms:
            ready_for_submission_blockers.append(
                CaseReadinessIssueRead(
                    code="unapproved_generated_forms",
                    message="All generated forms must be approved before ready_for_submission.",
                    severity="blocking",
                )
            )
        if not attorney_approved_review_exists:
            ready_for_submission_blockers.append(
                CaseReadinessIssueRead(
                    code="missing_attorney_approval",
                    message="An approved attorney review is required before ready_for_submission.",
                    severity="blocking",
                )
            )

        submitted_blockers = []
        submitted_warnings = self._build_high_inconsistency_warnings(open_high_inconsistencies)
        if not attorney_approved_review_exists:
            submitted_blockers.append(
                CaseReadinessIssueRead(
                    code="missing_attorney_approval",
                    message="An approved attorney review is required before submitted.",
                    severity="blocking",
                )
            )
        if case.status != "ready_for_submission":
            submitted_blockers.append(
                CaseReadinessIssueRead(
                    code="not_ready_for_submission",
                    message="Case must be in ready_for_submission before submitted.",
                    severity="blocking",
                )
            )

        targets = [
            CaseTargetReadinessRead(
                target_status="attorney_review",
                is_ready=len(attorney_review_blockers) == 0,
                blockers=attorney_review_blockers,
                warnings=attorney_review_warnings,
            ),
            CaseTargetReadinessRead(
                target_status="ready_for_submission",
                is_ready=len(ready_for_submission_blockers) == 0,
                blockers=ready_for_submission_blockers,
                warnings=ready_for_submission_warnings,
            ),
            CaseTargetReadinessRead(
                target_status="submitted",
                is_ready=len(submitted_blockers) == 0,
                blockers=submitted_blockers,
                warnings=submitted_warnings,
            ),
        ]

        return CaseReadinessRead(
            case_id=case.id,
            case_status=case.status,
            summary=summary,
            targets=targets,
        )

    def _build_document_blockers(self, missing_required_document_types: list[str]) -> list[CaseReadinessIssueRead]:
        blockers: list[CaseReadinessIssueRead] = []
        if missing_required_document_types:
            blockers.append(
                CaseReadinessIssueRead(
                    code="missing_required_documents",
                    message="Required documents are missing: " + ", ".join(missing_required_document_types),
                    severity="blocking",
                )
            )
        return blockers

    def _build_high_inconsistency_warnings(self, open_high_inconsistencies: list[object]) -> list[CaseReadinessIssueRead]:
        if not open_high_inconsistencies:
            return []
        return [
            CaseReadinessIssueRead(
                code="open_high_inconsistencies",
                message=f"{len(open_high_inconsistencies)} high-severity inconsistencies remain open.",
                severity="warning",
            )
        ]

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
        payload: dict,
    ) -> AuditLog:
        return await self.audit_log_repository.create(
            {
                "case_id": case_id,
                "entity_type": "case_readiness",
                "entity_id": str(entity_id),
                "action": action,
                "actor_reference": actor_reference,
                "payload": payload,
                "occurred_at": datetime.now(UTC),
            }
        )
