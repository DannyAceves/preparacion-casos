from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.inconsistency import Inconsistency
from app.repositories.audit_log import AuditLogRepository
from app.repositories.inconsistency import InconsistencyRepository
from app.schemas.inconsistency import InconsistencyActionRequest, InconsistencyCreateRequest

ALLOWED_INCONSISTENCY_STATUSES = {"open", "under_review", "resolved", "dismissed"}
ALLOWED_INCONSISTENCY_SEVERITIES = {"low", "medium", "high", "critical"}


class InconsistencyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = InconsistencyRepository(session)
        self.audit_log_repository = AuditLogRepository(session)

    async def list_for_case(self, case_id: uuid.UUID) -> list[Inconsistency]:
        await self._get_case(case_id)
        return await self.repository.list_for_case(case_id)

    async def create_for_case(
        self,
        case_id: uuid.UUID,
        payload: InconsistencyCreateRequest,
    ) -> Inconsistency:
        case = await self._get_case(case_id)
        self._validate_status(payload.status)
        self._validate_severity(payload.severity)

        inconsistency = await self.repository.create(
            {
                "case_id": case.id,
                "field_key": payload.field_key,
                "severity": payload.severity,
                "status": payload.status,
                "description": payload.description,
                "evidence_payload": payload.evidence_payload,
                "resolution_notes": None,
                "resolved_by_user_id": None,
                "resolved_at": None,
            }
        )
        await self._create_audit_log(
            case_id=case.id,
            entity_id=inconsistency.id,
            action="inconsistency_created",
            actor_reference=payload.actor_reference,
            payload={
                "case_id": str(case.id),
                "field_key": inconsistency.field_key,
                "severity": inconsistency.severity,
                "status": inconsistency.status,
            },
        )
        await self.session.commit()
        return inconsistency

    async def resolve_for_case(
        self,
        case_id: uuid.UUID,
        inconsistency_id: uuid.UUID,
        payload: InconsistencyActionRequest,
    ) -> Inconsistency:
        inconsistency = await self._get_inconsistency(case_id, inconsistency_id)
        updated = await self.repository.update(
            inconsistency,
            {
                "status": "resolved",
                "resolution_notes": payload.notes,
                "resolved_by_user_id": payload.actor_reference,
                "resolved_at": datetime.now(UTC),
            },
        )
        await self._create_audit_log(
            case_id=case_id,
            entity_id=updated.id,
            action="inconsistency_resolved",
            actor_reference=payload.actor_reference,
            payload={
                "case_id": str(case_id),
                "field_key": updated.field_key,
                "status": updated.status,
            },
        )
        await self.session.commit()
        return updated

    async def dismiss_for_case(
        self,
        case_id: uuid.UUID,
        inconsistency_id: uuid.UUID,
        payload: InconsistencyActionRequest,
    ) -> Inconsistency:
        inconsistency = await self._get_inconsistency(case_id, inconsistency_id)
        updated = await self.repository.update(
            inconsistency,
            {
                "status": "dismissed",
                "resolution_notes": payload.notes,
                "resolved_by_user_id": payload.actor_reference,
                "resolved_at": datetime.now(UTC),
            },
        )
        await self._create_audit_log(
            case_id=case_id,
            entity_id=updated.id,
            action="inconsistency_dismissed",
            actor_reference=payload.actor_reference,
            payload={
                "case_id": str(case_id),
                "field_key": updated.field_key,
                "status": updated.status,
            },
        )
        await self.session.commit()
        return updated

    async def _get_case(self, case_id: uuid.UUID) -> Case:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
        return case

    async def _get_inconsistency(self, case_id: uuid.UUID, inconsistency_id: uuid.UUID) -> Inconsistency:
        await self._get_case(case_id)
        inconsistency = await self.repository.get_for_case(case_id, inconsistency_id)
        if inconsistency is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="inconsistency not found")
        return inconsistency

    def _validate_status(self, status_value: str) -> None:
        if status_value not in ALLOWED_INCONSISTENCY_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid inconsistency status")

    def _validate_severity(self, severity_value: str) -> None:
        if severity_value not in ALLOWED_INCONSISTENCY_SEVERITIES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid inconsistency severity")

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
                "entity_type": "inconsistency",
                "entity_id": str(entity_id),
                "action": action,
                "actor_reference": actor_reference,
                "payload": payload,
                "occurred_at": datetime.now(UTC),
            }
        )
