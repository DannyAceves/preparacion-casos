from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.review import Review
from app.repositories.audit_log import AuditLogRepository
from app.repositories.review import ReviewRepository
from app.schemas.review import CaseReviewCreateRequest, TimelineEventRead

ALLOWED_REVIEW_TYPES = {"paralegal", "attorney", "qa"}
ALLOWED_REVIEW_DECISIONS = {"fix_required", "approved", "rejected"}


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.review_repository = ReviewRepository(session)
        self.audit_log_repository = AuditLogRepository(session)

    async def create_for_case(self, case_id: uuid.UUID, payload: CaseReviewCreateRequest) -> Review:
        await self._get_case(case_id)
        self._validate_review_type(payload.review_type)
        self._validate_decision(payload.decision)

        review = await self.review_repository.create(
            {
                "case_id": case_id,
                "review_type": payload.review_type,
                "reviewer_reference": payload.reviewer_reference,
                "decision": payload.decision,
                "notes": payload.notes,
                "reviewed_at": payload.reviewed_at or datetime.now(UTC),
            }
        )
        await self._create_audit_log(
            case_id=case_id,
            entity_id=review.id,
            action="review_created",
            actor_reference=payload.actor_reference or payload.reviewer_reference,
            payload={
                "review_type": review.review_type,
                "decision": review.decision,
            },
        )
        await self.session.commit()
        return review

    async def list_for_case(self, case_id: uuid.UUID) -> list[Review]:
        await self._get_case(case_id)
        return await self.review_repository.list_for_case(case_id)

    async def get_case_timeline(self, case_id: uuid.UUID) -> list[TimelineEventRead]:
        await self._get_case(case_id)
        reviews = await self.review_repository.list_for_case(case_id)
        audit_logs = await self.audit_log_repository.list_for_case(case_id)

        review_events = [
            TimelineEventRead(
                event_type="review",
                entity_type="review",
                entity_id=str(review.id),
                action=f"review_{review.decision}",
                actor_reference=review.reviewer_reference,
                occurred_at=review.reviewed_at or review.created_at,
                payload={
                    "review_type": review.review_type,
                    "decision": review.decision,
                    "notes": review.notes,
                },
            )
            for review in reviews
        ]
        audit_events = [
            TimelineEventRead(
                event_type="audit_log",
                entity_type=audit_log.entity_type,
                entity_id=audit_log.entity_id,
                action=audit_log.action,
                actor_reference=audit_log.actor_reference,
                occurred_at=audit_log.occurred_at,
                payload=audit_log.payload,
            )
            for audit_log in audit_logs
        ]

        events = review_events + audit_events
        return sorted(events, key=lambda item: item.occurred_at, reverse=True)

    async def _get_case(self, case_id: uuid.UUID) -> Case:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
        return case

    def _validate_review_type(self, review_type: str) -> None:
        if review_type not in ALLOWED_REVIEW_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid review type")

    def _validate_decision(self, decision: str) -> None:
        if decision not in ALLOWED_REVIEW_DECISIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid review decision")

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
                "entity_type": "review",
                "entity_id": str(entity_id),
                "action": action,
                "actor_reference": actor_reference,
                "payload": payload,
                "occurred_at": datetime.now(UTC),
            }
        )
