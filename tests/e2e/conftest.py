from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.api.deps import get_session_dependency
from app.main import app
from app.services.case import CaseService
from app.services.case_canonical_field import CaseCanonicalFieldService
from app.services.case_packet import CasePacketService
from app.services.case_questionnaire import CaseQuestionnaireService
from app.services.case_readiness import CaseReadinessService
from app.services.case_submission import CaseSubmissionService
from app.services.client import ClientService
from app.services.document_management import DocumentManagementService
from app.services.generated_form import GeneratedFormService
from app.services.inconsistency import InconsistencyService


class FakeSession:
    async def commit(self) -> None:
        return None


class WorkflowState:
    def __init__(self) -> None:
        self.clients: dict[uuid.UUID, dict[str, Any]] = {}
        self.cases: dict[uuid.UUID, dict[str, Any]] = {}
        self.questionnaires: dict[uuid.UUID, dict[str, Any]] = {}
        self.documents: dict[uuid.UUID, dict[str, Any]] = {}
        self.canonical_fields: dict[tuple[uuid.UUID, str], dict[str, Any]] = {}
        self.inconsistencies: dict[uuid.UUID, dict[str, Any]] = {}
        self.generated_forms: dict[uuid.UUID, dict[str, Any]] = {}
        self.packets: dict[uuid.UUID, dict[str, Any]] = {}
        self.submissions: dict[uuid.UUID, dict[str, Any]] = {}

    def now(self) -> datetime:
        return datetime.now(UTC)

    def timestamped(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = self.now()
        payload.setdefault("created_at", now)
        payload.setdefault("updated_at", now)
        return payload

    def readiness_for_case(self, case_id: uuid.UUID) -> dict[str, Any]:
        case = self.cases[case_id]
        current_documents = [
            document
            for document in self.documents.values()
            if document["case_id"] == case_id and document["is_current"]
        ]
        valid_document_types = {
            document["document_type"]
            for document in current_documents
            if document["document_status"] not in {"rejected", "archived"}
            and document["processing_status"] != "failed"
        }
        required_document_types = ["passport", "evidence"]
        if case["case_type"] == "family-based":
            required_document_types = ["passport", "birth_certificate", "marriage_certificate", "evidence"]
        missing_required_document_types = [
            item for item in required_document_types if item not in valid_document_types
        ]
        open_high = [
            item
            for item in self.inconsistencies.values()
            if item["case_id"] == case_id
            and item["status"] in {"open", "under_review"}
            and item["severity"] in {"high", "critical"}
        ]
        open_critical = [item for item in open_high if item["severity"] == "critical"]
        generated_forms = [item for item in self.generated_forms.values() if item["case_id"] == case_id]
        unapproved_forms = [item for item in generated_forms if item["status"] != "approved"]
        attorney_approved_review_exists = bool(case.get("attorney_review_approved", False))
        warning_items = (
            [{"code": "open_high_inconsistencies", "message": f"{len(open_high)} high-severity inconsistencies remain open.", "severity": "warning"}]
            if open_high
            else []
        )

        attorney_review_blockers: list[dict[str, Any]] = []
        if missing_required_document_types:
            attorney_review_blockers.append({"code": "missing_required_documents", "message": "Required documents are missing: " + ", ".join(missing_required_document_types), "severity": "blocking"})
        if not generated_forms:
            attorney_review_blockers.append({"code": "missing_generated_forms", "message": "At least one generated form is required before attorney review.", "severity": "blocking"})

        ready_blockers = list(attorney_review_blockers)
        if open_critical:
            ready_blockers.append({"code": "open_critical_inconsistencies", "message": "Critical inconsistencies must be resolved before ready_for_submission.", "severity": "blocking"})
        if unapproved_forms:
            ready_blockers.append({"code": "unapproved_generated_forms", "message": "All generated forms must be approved before ready_for_submission.", "severity": "blocking"})
        if not attorney_approved_review_exists:
            ready_blockers.append({"code": "missing_attorney_approval", "message": "An approved attorney review is required before ready_for_submission.", "severity": "blocking"})

        submitted_blockers: list[dict[str, Any]] = []
        if not attorney_approved_review_exists:
            submitted_blockers.append({"code": "missing_attorney_approval", "message": "An approved attorney review is required before submitted.", "severity": "blocking"})
        if case["status"] != "ready_for_submission":
            submitted_blockers.append({"code": "not_ready_for_submission", "message": "Case must be in ready_for_submission before submitted.", "severity": "blocking"})

        return {
            "case_id": case_id,
            "case_status": case["status"],
            "summary": {
                "required_document_types": required_document_types,
                "present_required_document_types": sorted(valid_document_types & set(required_document_types)),
                "missing_required_document_types": missing_required_document_types,
                "open_high_or_critical_inconsistency_count": len(open_high),
                "open_critical_inconsistency_count": len(open_critical),
                "unapproved_generated_form_count": len(unapproved_forms),
                "generated_form_count": len(generated_forms),
                "attorney_approved_review_exists": attorney_approved_review_exists,
            },
            "targets": [
                {"target_status": "attorney_review", "is_ready": len(attorney_review_blockers) == 0, "blockers": attorney_review_blockers, "warnings": warning_items},
                {"target_status": "ready_for_submission", "is_ready": len(ready_blockers) == 0, "blockers": ready_blockers, "warnings": warning_items},
                {"target_status": "submitted", "is_ready": len(submitted_blockers) == 0, "blockers": submitted_blockers, "warnings": warning_items},
            ],
        }


@pytest.fixture
def e2e_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, WorkflowState]:
    state = WorkflowState()

    async def fake_session_dependency() -> FakeSession:
        return FakeSession()

    async def create_client(self: ClientService, payload: Any) -> dict[str, Any]:
        client_id = uuid.uuid4()
        client = state.timestamped({"id": client_id, "first_name": payload.first_name, "last_name": payload.last_name, "email": payload.email, "phone": payload.phone, "date_of_birth": payload.date_of_birth, "notes": payload.notes})
        state.clients[client_id] = client
        return client

    async def create_case(self: CaseService, payload: Any) -> dict[str, Any]:
        if payload.client_id not in state.clients:
            raise HTTPException(status_code=404, detail="client not found")
        case_id = uuid.uuid4()
        case = state.timestamped({"id": case_id, "client_id": payload.client_id, "case_number": payload.case_number, "case_type": payload.case_type, "status": payload.status, "title": payload.title, "summary": payload.summary, "attorney_review_approved": False})
        state.cases[case_id] = case
        return case

    async def get_case(self: CaseService, case_id: uuid.UUID) -> dict[str, Any]:
        case = state.cases.get(case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="case not found")
        return case

    async def get_case_questionnaire(self: CaseQuestionnaireService, case_id: uuid.UUID) -> dict[str, Any]:
        questionnaire = state.questionnaires.get(case_id)
        if questionnaire is not None:
            return questionnaire
        full_name_question_id = uuid.uuid4()
        dob_question_id = uuid.uuid4()
        questionnaire = {
            "case_id": case_id,
            "case_type": state.cases[case_id]["case_type"],
            "questionnaire": {"id": uuid.uuid4(), "case_type": state.cases[case_id]["case_type"], "title": "E2E Intake Questionnaire", "description": "E2E questionnaire template", "status": "active", "version": 1},
            "sections": [
                {
                    "id": uuid.uuid4(),
                    "title": "Beneficiary Information",
                    "description": "Core applicant fields",
                    "display_order": 1,
                    "questions": [
                        {"id": full_name_question_id, "key": "beneficiary.full_name", "prompt": "What is the beneficiary full legal name?", "help_text": None, "input_type": "text", "is_required": True, "display_order": 1, "options": None, "validation_rules": None, "answer": None},
                        {"id": dob_question_id, "key": "beneficiary.date_of_birth", "prompt": "What is the beneficiary date of birth?", "help_text": None, "input_type": "date", "is_required": True, "display_order": 2, "options": None, "validation_rules": None, "answer": None},
                    ],
                }
            ],
        }
        state.questionnaires[case_id] = questionnaire
        return questionnaire

    async def upsert_answers(self: CaseQuestionnaireService, case_id: uuid.UUID, payload: Any) -> list[dict[str, Any]]:
        questionnaire = await get_case_questionnaire(self, case_id)
        question_map = {question["id"]: question for section in questionnaire["sections"] for question in section["questions"]}
        answers: list[dict[str, Any]] = []
        for item in payload.answers:
            question = question_map[item.question_id]
            answer = question.get("answer")
            if answer is None:
                answer = state.timestamped({"id": uuid.uuid4(), "case_id": case_id, "question_id": item.question_id})
                question["answer"] = answer
            answer.update({"answer_text": item.value.answer_text, "answer_date": item.value.answer_date, "answer_boolean": item.value.answer_boolean, "answer_choice": item.value.answer_choice, "answer_choices": item.value.answer_choices, "answer_json": item.value.answer_json, "updated_at": state.now()})
            answers.append(answer)
        return answers

    async def upload_document(self: DocumentManagementService, case_id: uuid.UUID, uploaded_by_user_id: str, file: Any, document_status: str = "uploaded", classification_label: str | None = None, classification_source: str | None = None) -> dict[str, Any]:
        if case_id not in state.cases:
            raise HTTPException(status_code=404, detail="case not found")
        document_id = uuid.uuid4()
        now = state.now()
        file_bytes = file.file.read()
        document = state.timestamped({"id": document_id, "case_id": case_id, "uploaded_by_user_id": uploaded_by_user_id, "document_type": classification_label or "unclassified", "original_filename": file.filename, "stored_filename": f"{document_id}-{file.filename}", "storage_backend": "local", "storage_key": f"/tmp/{document_id}-{file.filename}", "mime_type": file.content_type or "application/octet-stream", "size_bytes": len(file_bytes), "sha256_hash": uuid.uuid4().hex + uuid.uuid4().hex, "document_status": document_status, "processing_status": "queued", "classification_label": classification_label, "classification_source": classification_source, "classification_confidence_score": 0.88 if classification_label else None, "file_metadata": {"seeded": False}, "extracted_text": None, "extracted_fields": None, "extracted_metadata": None, "version_number": 1, "is_current": True, "previous_version_id": None, "root_document_id": document_id, "replacement_notes": None, "uploaded_at": now})
        state.documents[document_id] = document
        return document

    async def get_document_detail(self: DocumentManagementService, document_id: uuid.UUID) -> dict[str, Any]:
        document = state.documents.get(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="document not found")
        lineage = [item for item in state.documents.values() if item["root_document_id"] == document["root_document_id"]]
        return {**document, "versions": sorted(lineage, key=lambda item: item["version_number"])}

    async def list_case_documents(self: DocumentManagementService, case_id: uuid.UUID) -> list[dict[str, Any]]:
        return [item for item in state.documents.values() if item["case_id"] == case_id and item["is_current"]]

    async def enqueue_reprocessing(self: DocumentManagementService, document_id: uuid.UUID, actor_reference: str | None) -> None:
        document = state.documents.get(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="document not found")
        case_id = document["case_id"]
        document["processing_status"] = "processed"
        document["document_status"] = "processed"
        document["updated_at"] = state.now()
        state.canonical_fields[(case_id, "beneficiary.full_name")] = state.timestamped({"id": uuid.uuid4(), "case_id": case_id, "source_document_id": document_id, "field_key": "beneficiary.full_name", "field_value": "QA Applicant", "confidence_score": Decimal("0.9300"), "source_priority": 100, "status": "confirmed"})
        inconsistency_id = uuid.uuid4()
        state.inconsistencies[inconsistency_id] = state.timestamped({"id": inconsistency_id, "case_id": case_id, "field_key": "beneficiary.date_of_birth", "severity": "critical", "status": "open", "description": "DOB from document does not match questionnaire answer.", "evidence_payload": {"sources": ["questionnaire", "document"]}, "resolution_notes": None, "resolved_by_user_id": None, "resolved_at": None})

    async def list_canonical_fields(self: CaseCanonicalFieldService, case_id: uuid.UUID) -> list[dict[str, Any]]:
        return [value for (stored_case_id, _), value in state.canonical_fields.items() if stored_case_id == case_id]

    async def upsert_canonical_field(self: CaseCanonicalFieldService, case_id: uuid.UUID, field_key: str, payload: Any) -> dict[str, Any]:
        existing = state.canonical_fields.get((case_id, field_key))
        if existing is None:
            existing = state.timestamped({"id": uuid.uuid4(), "case_id": case_id, "source_document_id": payload.source_document_id, "field_key": field_key, "field_value": payload.field_value, "confidence_score": payload.confidence_score, "source_priority": payload.source_priority or 0, "status": payload.status or "suggested"})
            state.canonical_fields[(case_id, field_key)] = existing
        else:
            if payload.source_document_id is not None:
                existing["source_document_id"] = payload.source_document_id
            if payload.field_value is not None:
                existing["field_value"] = payload.field_value
            if payload.confidence_score is not None:
                existing["confidence_score"] = payload.confidence_score
            if payload.source_priority is not None:
                existing["source_priority"] = payload.source_priority
            if payload.status is not None:
                existing["status"] = payload.status
            existing["updated_at"] = state.now()
        return existing

    async def list_inconsistencies(self: InconsistencyService, case_id: uuid.UUID) -> list[dict[str, Any]]:
        return [value for value in state.inconsistencies.values() if value["case_id"] == case_id]

    async def resolve_inconsistency(self: InconsistencyService, case_id: uuid.UUID, inconsistency_id: uuid.UUID, payload: Any) -> dict[str, Any]:
        inconsistency = state.inconsistencies.get(inconsistency_id)
        if inconsistency is None or inconsistency["case_id"] != case_id:
            raise HTTPException(status_code=404, detail="inconsistency not found")
        inconsistency["status"] = "resolved"
        inconsistency["resolution_notes"] = payload.notes
        inconsistency["resolved_by_user_id"] = payload.actor_reference
        inconsistency["resolved_at"] = state.now()
        inconsistency["updated_at"] = state.now()
        return inconsistency

    async def dismiss_inconsistency(self: InconsistencyService, case_id: uuid.UUID, inconsistency_id: uuid.UUID, payload: Any) -> dict[str, Any]:
        inconsistency = state.inconsistencies.get(inconsistency_id)
        if inconsistency is None or inconsistency["case_id"] != case_id:
            raise HTTPException(status_code=404, detail="inconsistency not found")
        inconsistency["status"] = "dismissed"
        inconsistency["resolution_notes"] = payload.notes
        inconsistency["resolved_by_user_id"] = payload.actor_reference
        inconsistency["resolved_at"] = state.now()
        inconsistency["updated_at"] = state.now()
        return inconsistency

    async def generate_forms(self: GeneratedFormService, case_id: uuid.UUID, payload: Any) -> list[dict[str, Any]]:
        case = state.cases[case_id]
        form_id = uuid.uuid4()
        generated_form_id = uuid.uuid4()
        warnings = []
        if (case_id, "beneficiary.date_of_birth") not in state.canonical_fields:
            warnings.append({"type": "missing_required_field", "form_field_key": "beneficiary.date_of_birth", "canonical_field_key": "beneficiary.date_of_birth", "message": "Required canonical field is missing."})
        generated_form = state.timestamped({"id": generated_form_id, "case_id": case_id, "form_id": form_id, "draft_version": 1, "status": "review_pending" if warnings else "draft", "generated_payload": {"form_code": "I-130" if case["case_type"] == "family-based" else "GEN-001", "form_name": "Petition Form", "form_version": 1, "fields": {"beneficiary.full_name": state.canonical_fields.get((case_id, "beneficiary.full_name"), {}).get("field_value"), "beneficiary.date_of_birth": state.canonical_fields.get((case_id, "beneficiary.date_of_birth"), {}).get("field_value")}}, "warnings_payload": warnings or None, "export_path": f"{payload.export_base_path or '/tmp/forms'}/{case['case_number']}/draft-v1.json", "review_notes": None, "generated_at": state.now(), "reviewed_by_user_id": None, "reviewed_at": None, "form": {"form_id": form_id, "form_code": "I-130" if case['case_type'] == 'family-based' else 'GEN-001', "form_name": "Petition Form", "version": 1, "case_type_id": case["case_type"]}})
        state.generated_forms[generated_form_id] = generated_form
        return [generated_form]

    async def list_forms(self: GeneratedFormService, case_id: uuid.UUID) -> list[dict[str, Any]]:
        return [item for item in state.generated_forms.values() if item["case_id"] == case_id]

    async def get_generated_form_detail(self: GeneratedFormService, generated_form_id: uuid.UUID) -> dict[str, Any]:
        item = state.generated_forms.get(generated_form_id)
        if item is None:
            raise HTTPException(status_code=404, detail="generated form not found")
        return {**item, "form": item["form"]}

    async def approve_generated_form(self: GeneratedFormService, generated_form_id: uuid.UUID, payload: Any) -> dict[str, Any]:
        item = state.generated_forms[generated_form_id]
        item["status"] = "approved"
        item["review_notes"] = payload.review_notes
        item["reviewed_by_user_id"] = payload.reviewed_by_user_id
        item["reviewed_at"] = state.now()
        item["updated_at"] = state.now()
        state.cases[item["case_id"]]["attorney_review_approved"] = True
        return item

    async def mark_generated_form_fix_required(self: GeneratedFormService, generated_form_id: uuid.UUID, payload: Any) -> dict[str, Any]:
        item = state.generated_forms[generated_form_id]
        item["status"] = "fix_required"
        item["review_notes"] = payload.review_notes
        item["reviewed_by_user_id"] = payload.reviewed_by_user_id
        item["reviewed_at"] = state.now()
        item["updated_at"] = state.now()
        return item

    async def generate_packet(self: CasePacketService, case_id: uuid.UUID, payload: Any) -> dict[str, Any]:
        case = state.cases[case_id]
        client = state.clients[case["client_id"]]
        documents = await list_case_documents(None, case_id)
        packet = state.timestamped({"id": uuid.uuid4(), "case_id": case_id, "packet_version": 1, "packet_status": "generated", "generated_by_reference": payload.generated_by_reference, "summary_payload": {"case_id": case_id, "case_number": case["case_number"], "case_type": case["case_type"], "case_status": case["status"], "title": case["title"], "client": {"id": client["id"], "full_name": f"{client['first_name']} {client['last_name']}", "email": client["email"], "phone": client["phone"]}, "participants": [], "canonical_fields": [{"field_key": field_key, "field_value": item["field_value"], "status": item["status"]} for (stored_case_id, field_key), item in state.canonical_fields.items() if stored_case_id == case_id], "open_inconsistency_count": len([item for item in state.inconsistencies.values() if item["case_id"] == case_id and item["status"] in {"open", "under_review"}]), "latest_review": None}, "document_index": [{"document_id": item["id"], "document_type": item["document_type"], "title": item["original_filename"], "original_filename": item["original_filename"], "classification_label": item["classification_label"], "classification_confidence_score": item["classification_confidence_score"], "document_status": item["document_status"], "processing_status": item["processing_status"], "priority": index, "section": "Supporting Documents", "uploaded_at": item["uploaded_at"]} for index, item in enumerate(documents, start=1)], "checklist_payload": [{"item_key": f"document:{item['document_type']}", "label": item["document_type"], "status": "ready", "required": True, "related_document_type": item["document_type"], "notes": None} for item in documents], "export_artifact": {"artifact_type": "case_review_packet", "format": "json", "generated_at": state.now(), "packet_version": 1, "sections": [], "prefilled_forms_placeholder": {"ready": True}}, "generation_notes": payload.generation_notes, "generated_at": state.now()})
        state.packets[case_id] = packet
        return packet

    async def get_packet(self: CasePacketService, case_id: uuid.UUID) -> dict[str, Any]:
        packet = state.packets.get(case_id)
        if packet is None:
            raise HTTPException(status_code=404, detail="case packet not found")
        return packet

    async def get_readiness(self: CaseReadinessService, case_id: uuid.UUID) -> dict[str, Any]:
        return state.readiness_for_case(case_id)

    async def validate_readiness(self: CaseReadinessService, case_id: uuid.UUID, payload: Any) -> dict[str, Any]:
        return state.readiness_for_case(case_id)

    async def transition_case(self: CaseReadinessService, case_id: uuid.UUID, payload: Any) -> dict[str, Any]:
        readiness = state.readiness_for_case(case_id)
        target = next(item for item in readiness["targets"] if item["target_status"] == payload.target_status)
        if not target["is_ready"]:
            raise HTTPException(status_code=400, detail={"message": f"case cannot transition to '{payload.target_status}'", "blockers": target["blockers"]})
        state.cases[case_id]["status"] = payload.target_status
        state.cases[case_id]["updated_at"] = state.now()
        return state.cases[case_id]

    async def approve_submission(self: CaseSubmissionService, case_id: uuid.UUID, payload: Any) -> dict[str, Any]:
        await transition_case(None, case_id, type("Payload", (), {"target_status": "ready_for_submission"})())
        submission = state.submissions.get(case_id)
        if submission is None:
            submission = state.timestamped({"id": uuid.uuid4(), "case_id": case_id, "status": "draft", "approved_for_submission_at": None, "approved_by_user_id": None, "submitted_at": None, "submitted_by_user_id": None, "submission_reference": None, "failed_at": None, "failed_by_user_id": None, "failure_reason": None})
            state.submissions[case_id] = submission
        submission["status"] = "approved_for_submission"
        submission["approved_for_submission_at"] = state.now()
        submission["approved_by_user_id"] = payload.approved_by_user_id
        submission["updated_at"] = state.now()
        return submission

    async def submit_case(self: CaseSubmissionService, case_id: uuid.UUID, payload: Any) -> dict[str, Any]:
        submission = state.submissions.get(case_id)
        if submission is None or submission["status"] != "approved_for_submission":
            raise HTTPException(status_code=400, detail="case submission must be approved before submit")
        state.cases[case_id]["status"] = "submitted"
        state.cases[case_id]["updated_at"] = state.now()
        submission["status"] = "submitted"
        submission["submitted_at"] = state.now()
        submission["submitted_by_user_id"] = payload.submitted_by_user_id
        submission["submission_reference"] = payload.submission_reference
        submission["updated_at"] = state.now()
        return submission

    async def close_case(self: CaseSubmissionService, case_id: uuid.UUID, payload: Any) -> dict[str, Any]:
        case = state.cases[case_id]
        submission = state.submissions.get(case_id)
        if case["status"] != "submitted" and (submission is None or submission["status"] not in {"submitted", "failed"}):
            raise HTTPException(status_code=400, detail="case can only be closed after submitted or failed submission")
        case["status"] = "closed"
        case["updated_at"] = state.now()
        return case

    async def get_submission(self: CaseSubmissionService, case_id: uuid.UUID) -> dict[str, Any]:
        submission = state.submissions.get(case_id)
        if submission is None:
            raise HTTPException(status_code=404, detail="case submission not found")
        return submission

    app.dependency_overrides[get_session_dependency] = fake_session_dependency
    monkeypatch.setattr(ClientService, "create", create_client)
    monkeypatch.setattr(CaseService, "create", create_case)
    monkeypatch.setattr(CaseService, "get", get_case)
    monkeypatch.setattr(CaseQuestionnaireService, "get_case_questionnaire", get_case_questionnaire)
    monkeypatch.setattr(CaseQuestionnaireService, "upsert_answers", upsert_answers)
    monkeypatch.setattr(DocumentManagementService, "upload_document", upload_document)
    monkeypatch.setattr(DocumentManagementService, "get_document_detail", get_document_detail)
    monkeypatch.setattr(DocumentManagementService, "list_case_documents", list_case_documents)
    monkeypatch.setattr(DocumentManagementService, "enqueue_reprocessing", enqueue_reprocessing)
    monkeypatch.setattr(CaseCanonicalFieldService, "list_for_case", list_canonical_fields)
    monkeypatch.setattr(CaseCanonicalFieldService, "upsert_by_field_key", upsert_canonical_field)
    monkeypatch.setattr(InconsistencyService, "list_for_case", list_inconsistencies)
    monkeypatch.setattr(InconsistencyService, "resolve_for_case", resolve_inconsistency)
    monkeypatch.setattr(InconsistencyService, "dismiss_for_case", dismiss_inconsistency)
    monkeypatch.setattr(GeneratedFormService, "generate_for_case", generate_forms)
    monkeypatch.setattr(GeneratedFormService, "list_for_case", list_forms)
    monkeypatch.setattr(GeneratedFormService, "get_detail", get_generated_form_detail)
    monkeypatch.setattr(GeneratedFormService, "approve", approve_generated_form)
    monkeypatch.setattr(GeneratedFormService, "mark_fix_required", mark_generated_form_fix_required)
    monkeypatch.setattr(CasePacketService, "generate_for_case", generate_packet)
    monkeypatch.setattr(CasePacketService, "get_latest_for_case", get_packet)
    monkeypatch.setattr(CaseReadinessService, "get_readiness", get_readiness)
    monkeypatch.setattr(CaseReadinessService, "validate_readiness", validate_readiness)
    monkeypatch.setattr(CaseReadinessService, "transition_case", transition_case)
    monkeypatch.setattr(CaseSubmissionService, "approve_for_submission", approve_submission)
    monkeypatch.setattr(CaseSubmissionService, "submit", submit_case)
    monkeypatch.setattr(CaseSubmissionService, "close_case", close_case)
    monkeypatch.setattr(CaseSubmissionService, "get_for_case", get_submission)

    with TestClient(app) as client:
        yield client, state

    app.dependency_overrides.clear()
