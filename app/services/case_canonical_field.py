from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.case_canonical_field import CaseCanonicalField
from app.models.document import Document
from app.repositories.audit_log import AuditLogRepository
from app.repositories.case_canonical_field import CaseCanonicalFieldRepository
from app.schemas.case_canonical_field import CaseCanonicalFieldPatchRequest

ALLOWED_CANONICAL_FIELD_STATUSES = {"suggested", "confirmed", "approved", "rejected"}


class CaseCanonicalFieldService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = CaseCanonicalFieldRepository(session)
        self.audit_log_repository = AuditLogRepository(session)

    async def list_for_case(self, case_id: uuid.UUID) -> list[CaseCanonicalField]:
        await self._get_case(case_id)
        return await self.repository.list_for_case(case_id)

    async def upsert_by_field_key(
        self,
        *,
        case_id: uuid.UUID,
        field_key: str,
        payload: CaseCanonicalFieldPatchRequest,
    ) -> CaseCanonicalField:
        case = await self._get_case(case_id)
        if payload.source_document_id is not None:
            await self._get_document(payload.source_document_id)
        if payload.status is not None and payload.status not in ALLOWED_CANONICAL_FIELD_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid canonical field status")

        existing = await self.repository.get_by_case_and_field_key(case.id, field_key)
        update_data = self._build_update_data(payload)

        if existing is None:
            created = await self.repository.create(
                {
                    "case_id": case.id,
                    "field_key": field_key,
                    "field_value": payload.field_value,
                    "confidence_score": self._to_float(payload.confidence_score),
                    "source_priority": payload.source_priority if payload.source_priority is not None else 0,
                    "status": payload.status or "suggested",
                    "source_document_id": payload.source_document_id,
                }
            )
            await self._create_audit_log(
                case_id=case.id,
                entity_id=created.id,
                action="canonical_field_created",
                actor_reference=payload.actor_reference,
                payload={
                    "case_id": str(case.id),
                    "field_key": field_key,
                    "status": created.status,
                },
            )
            await self.session.commit()
            return created

        updated = await self.repository.update(existing, update_data)
        await self._create_audit_log(
            case_id=case.id,
            entity_id=updated.id,
            action="canonical_field_updated",
            actor_reference=payload.actor_reference,
            payload={
                "case_id": str(case.id),
                "field_key": field_key,
                "status": updated.status,
            },
        )
        await self.session.commit()
        return updated

    def _build_update_data(self, payload: CaseCanonicalFieldPatchRequest) -> dict[str, Any]:
        data = payload.model_dump(exclude_unset=True, exclude={"actor_reference"})
        if "confidence_score" in data:
            data["confidence_score"] = self._to_float(payload.confidence_score)
        return data

    def _to_float(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None

    async def _get_case(self, case_id: uuid.UUID) -> Case:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
        return case

    async def _get_document(self, document_id: uuid.UUID) -> Document:
        document = await self.session.get(Document, document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document not found")
        return document

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
                "entity_type": "canonical_case_field",
                "entity_id": str(entity_id),
                "action": action,
                "actor_reference": actor_reference,
                "payload": payload,
                "occurred_at": datetime.now(UTC),
            }
        )
