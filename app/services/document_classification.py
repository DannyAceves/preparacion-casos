from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.document_classification import DocumentClassification
from app.repositories.audit_log import AuditLogRepository
from app.repositories.document import DocumentRepository
from app.repositories.document_classification import DocumentClassificationRepository
from app.schemas.document import DocumentClassificationUpdate
from app.schemas.document_classification import DocumentClassificationCreate


@dataclass(frozen=True)
class ClassificationCandidate:
    predicted_type: str
    confidence_score: float
    classification_method: str
    evidence_payload: dict[str, Any]


@dataclass(frozen=True)
class ClassificationResult:
    classification: DocumentClassification
    idempotent: bool


class RuleBasedDocumentClassifier:
    def __init__(self) -> None:
        self.filename_rules: dict[str, tuple[str, ...]] = {
            "passport": ("passport", "pasaporte"),
            "birth_certificate": ("birth certificate", "acta de nacimiento", "certificate of birth"),
            "marriage_certificate": ("marriage certificate", "acta de matrimonio", "certificate of marriage"),
            "id": ("driver license", "license", "identification", "identidad", "id card", "credencial"),
            "evidence": ("evidence", "proof", "affidavit", "utility bill", "bank statement", "lease", "photo"),
        }
        self.text_rules: dict[str, tuple[str, ...]] = {
            "passport": (
                "passport",
                "pasaporte",
                "passport no",
                "passport number",
                "nationality",
                "date of birth",
            ),
            "birth_certificate": (
                "birth certificate",
                "acta de nacimiento",
                "certificate of live birth",
                "place of birth",
            ),
            "marriage_certificate": (
                "marriage certificate",
                "acta de matrimonio",
                "certificate of marriage",
                "date of marriage",
            ),
            "id": (
                "driver license",
                "identification card",
                "national id",
                "document number",
                "fecha de expedicion",
            ),
            "evidence": (
                "affidavit",
                "supporting evidence",
                "utility bill",
                "bank statement",
                "supporting document",
                "proof of",
            ),
        }

    def classify(self, document: Document) -> ClassificationCandidate:
        filename = self._normalize_text(document.original_filename)
        extracted_text = self._normalize_text(document.extracted_text or "")
        candidates: list[ClassificationCandidate] = []

        for label, keywords in self.filename_rules.items():
            matches = [keyword for keyword in keywords if keyword in filename]
            if matches:
                candidates.append(
                    ClassificationCandidate(
                        predicted_type=label,
                        confidence_score=min(0.95, 0.82 + (0.05 * len(matches))),
                        classification_method="filename_rules",
                        evidence_payload={"filename_matches": matches},
                    )
                )

        for label, keywords in self.text_rules.items():
            matches = [keyword for keyword in keywords if keyword in extracted_text]
            if matches:
                candidates.append(
                    ClassificationCandidate(
                        predicted_type=label,
                        confidence_score=min(0.96, 0.76 + (0.04 * len(matches))),
                        classification_method="text_rules",
                        evidence_payload={"text_matches": matches},
                    )
                )

        if filename.endswith((".jpg", ".jpeg", ".png")) and not candidates:
            candidates.append(
                ClassificationCandidate(
                    predicted_type="id",
                    confidence_score=0.45,
                    classification_method="image_fallback",
                    evidence_payload={"reason": "generic_image_document"},
                )
            )

        if not candidates:
            return ClassificationCandidate(
                predicted_type="unclassified",
                confidence_score=0.2,
                classification_method="fallback",
                evidence_payload={"reason": "no_rule_match"},
            )

        best_candidate = max(candidates, key=lambda item: item.confidence_score)
        merged_evidence: dict[str, Any] = {"candidates": [candidate.__dict__ for candidate in candidates]}
        merged_evidence.update(best_candidate.evidence_payload)
        return ClassificationCandidate(
            predicted_type=best_candidate.predicted_type,
            confidence_score=best_candidate.confidence_score,
            classification_method=best_candidate.classification_method,
            evidence_payload=merged_evidence,
        )

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.lower()).strip()


class DocumentClassificationService:
    def __init__(self, session: AsyncSession, classifier: RuleBasedDocumentClassifier | None = None) -> None:
        self.session = session
        self.classifier = classifier or RuleBasedDocumentClassifier()
        self.document_repository = DocumentRepository(session)
        self.classification_repository = DocumentClassificationRepository(session)
        self.audit_log_repository = AuditLogRepository(session)

    async def classify_document(
        self,
        *,
        document: Document,
        actor_reference: str | None,
        trigger: str | None,
        force_reprocess: bool = False,
    ) -> ClassificationResult:
        active = await self.classification_repository.get_active_for_document(document.id)
        if active is not None and active.classification_source == "manual" and not force_reprocess:
            await self._sync_document_classification(document, active)
            return ClassificationResult(classification=active, idempotent=True)

        if active is not None and active.classification_source == "automatic" and not force_reprocess:
            await self._sync_document_classification(document, active)
            return ClassificationResult(classification=active, idempotent=True)

        candidate = self.classifier.classify(document)
        classification = await self._replace_active_classification(
            document=document,
            predicted_type=candidate.predicted_type,
            confidence_score=candidate.confidence_score,
            classification_source="automatic",
            classification_method=candidate.classification_method,
            actor_reference=actor_reference,
            review_notes=None,
            reviewed_by_user_id=None,
            evidence_payload={
                **candidate.evidence_payload,
                "trigger": trigger,
                "force_reprocess": force_reprocess,
            },
            audit_action="document_classified",
        )
        return ClassificationResult(classification=classification, idempotent=False)

    async def review_document_classification(
        self,
        *,
        document: Document,
        payload: DocumentClassificationUpdate,
    ) -> DocumentClassification:
        classification_source = payload.classification_source
        audit_action = "document_classification_overridden" if classification_source == "manual" else "document_classification_reviewed"
        return await self._replace_active_classification(
            document=document,
            predicted_type=payload.classification_label,
            confidence_score=payload.classification_confidence_score if payload.classification_confidence_score is not None else 1.0,
            classification_source=classification_source,
            classification_method="manual_review",
            actor_reference=payload.reviewed_by_user_id,
            review_notes=payload.review_notes,
            reviewed_by_user_id=payload.reviewed_by_user_id,
            evidence_payload={"review_notes": payload.review_notes},
            audit_action=audit_action,
        )

    async def list_for_document(self, document_id: uuid.UUID) -> list[DocumentClassification]:
        return await self.classification_repository.list_for_document(document_id)

    async def _replace_active_classification(
        self,
        *,
        document: Document,
        predicted_type: str,
        confidence_score: float | None,
        classification_source: str,
        classification_method: str,
        actor_reference: str | None,
        review_notes: str | None,
        reviewed_by_user_id: str | None,
        evidence_payload: dict[str, Any] | list[Any] | None,
        audit_action: str,
    ) -> DocumentClassification:
        await self.classification_repository.deactivate_active_for_document(document.id)
        classification = await self.classification_repository.create(
            DocumentClassificationCreate(
                case_id=document.case_id,
                document_id=document.id,
                version_number=document.version_number,
                predicted_type=predicted_type,
                confidence_score=confidence_score,
                classification_source=classification_source,
                classification_method=classification_method,
                is_override=classification_source == "manual",
                is_active=True,
                reviewed_by_user_id=reviewed_by_user_id,
                review_notes=review_notes,
                evidence_payload=evidence_payload,
            ).model_dump()
        )
        await self._sync_document_classification(document, classification)
        await self._create_audit_log(
            case_id=document.case_id,
            entity_id=document.id,
            action=audit_action,
            actor_reference=actor_reference,
            payload={
                "document_id": str(document.id),
                "predicted_type": predicted_type,
                "confidence_score": confidence_score,
                "classification_source": classification_source,
                "classification_method": classification_method,
            },
        )
        return classification

    async def _sync_document_classification(
        self,
        document: Document,
        classification: DocumentClassification,
    ) -> Document:
        return await self.document_repository.update(
            document,
            {
                "document_type": classification.predicted_type,
                "classification_label": classification.predicted_type,
                "classification_source": classification.classification_source,
                "classification_confidence_score": classification.confidence_score,
            },
        )

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
                "entity_type": "document_classification",
                "entity_id": str(entity_id),
                "action": action,
                "actor_reference": actor_reference,
                "payload": payload,
                "occurred_at": datetime.now(UTC),
            }
        )
