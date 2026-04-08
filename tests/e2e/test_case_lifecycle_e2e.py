from __future__ import annotations

from datetime import date
from typing import Any

from fastapi.testclient import TestClient


def assert_status(response, expected: int) -> None:
    assert response.status_code == expected, f"Expected {expected}, got {response.status_code}. Body: {response.text}"


def test_main_case_lifecycle_happy_path(e2e_client: tuple[TestClient, Any]) -> None:
    client, _ = e2e_client

    client_response = client.post(
        "/api/v1/clients",
        json={
            "first_name": "E2E",
            "last_name": "Applicant",
            "email": "e2e.applicant@example.com",
            "phone": "+52-555-000-1111",
            "date_of_birth": "1994-04-12",
            "notes": "Created from e2e suite.",
        },
    )
    assert_status(client_response, 201)
    client_id = client_response.json()["id"]

    case_response = client.post(
        "/api/v1/cases",
        json={
            "client_id": client_id,
            "case_number": "CASE-E2E-0001",
            "case_type": "family-based",
            "status": "draft",
            "title": "E2E family-based flow",
            "summary": "Covers the main happy path from intake to closure.",
        },
    )
    assert_status(case_response, 201)
    case_id = case_response.json()["id"]

    questionnaire_response = client.get(f"/api/v1/cases/{case_id}/questionnaire")
    assert_status(questionnaire_response, 200)
    questions = questionnaire_response.json()["sections"][0]["questions"]
    full_name_question_id = questions[0]["id"]
    dob_question_id = questions[1]["id"]

    answers_response = client.post(
        f"/api/v1/cases/{case_id}/questionnaire/answers",
        json={
            "actor_reference": "staff-paralegal-001",
            "answers": [
                {"question_id": full_name_question_id, "value": {"answer_text": "QA Applicant"}},
                {"question_id": dob_question_id, "value": {"answer_date": str(date(1994, 4, 12))}},
            ],
        },
    )
    assert_status(answers_response, 201)

    upload_response = client.post(
        f"/api/v1/cases/{case_id}/documents/upload",
        data={
            "uploaded_by_user_id": "staff-paralegal-001",
            "document_status": "uploaded",
            "classification_label": "passport",
            "classification_source": "manual",
        },
        files={"file": ("passport.pdf", b"seed pdf bytes", "application/pdf")},
    )
    assert_status(upload_response, 201)
    document_id = upload_response.json()["id"]

    reprocess_response = client.post(
        f"/api/v1/documents/{document_id}/reprocess",
        json={"actor_reference": "staff-paralegal-001"},
    )
    assert_status(reprocess_response, 202)

    canonical_list_response = client.get(f"/api/v1/cases/{case_id}/canonical-fields")
    assert_status(canonical_list_response, 200)
    assert len(canonical_list_response.json()) >= 1, canonical_list_response.text

    canonical_patch_response = client.patch(
        f"/api/v1/cases/{case_id}/canonical-fields/beneficiary.date_of_birth",
        json={
            "actor_reference": "staff-paralegal-001",
            "field_value": "1994-04-12",
            "confidence_score": 0.98,
            "source_priority": 100,
            "status": "approved",
        },
    )
    assert_status(canonical_patch_response, 200)

    inconsistencies_response = client.get(f"/api/v1/cases/{case_id}/inconsistencies")
    assert_status(inconsistencies_response, 200)
    inconsistency_id = inconsistencies_response.json()[0]["id"]

    resolve_response = client.post(
        f"/api/v1/cases/{case_id}/inconsistencies/{inconsistency_id}/resolve",
        json={"actor_reference": "staff-attorney-001", "notes": "DOB aligned with passport and questionnaire."},
    )
    assert_status(resolve_response, 200)
    assert resolve_response.json()["status"] == "resolved"

    forms_generate_response = client.post(
        f"/api/v1/cases/{case_id}/forms/generate",
        json={"generated_by_reference": "staff-paralegal-001", "export_base_path": "/tmp/forms"},
    )
    assert_status(forms_generate_response, 201)
    generated_form_id = forms_generate_response.json()[0]["id"]

    generated_form_detail_response = client.get(f"/api/v1/generated-forms/{generated_form_id}")
    assert_status(generated_form_detail_response, 200)

    generated_form_approve_response = client.post(
        f"/api/v1/generated-forms/{generated_form_id}/approve",
        json={"reviewed_by_user_id": "staff-attorney-001", "review_notes": "Approved in e2e suite."},
    )
    assert_status(generated_form_approve_response, 200)
    assert generated_form_approve_response.json()["status"] == "approved"

    packet_response = client.post(
        f"/api/v1/cases/{case_id}/packet/generate",
        json={"generated_by_reference": "staff-paralegal-001", "generation_notes": "E2E packet generation."},
    )
    assert_status(packet_response, 201)

    readiness_response = client.post(
        f"/api/v1/cases/{case_id}/validate-readiness",
        json={"actor_reference": "staff-attorney-001"},
    )
    assert_status(readiness_response, 200)
    ready_target = next(item for item in readiness_response.json()["targets"] if item["target_status"] == "ready_for_submission")
    assert ready_target["is_ready"] is True, readiness_response.text

    approve_submission_response = client.post(
        f"/api/v1/cases/{case_id}/submission/approve",
        json={"approved_by_user_id": "staff-attorney-001", "notes": "Approved for filing."},
    )
    assert_status(approve_submission_response, 200)
    assert approve_submission_response.json()["status"] == "approved_for_submission"

    submit_response = client.post(
        f"/api/v1/cases/{case_id}/submission/submit",
        json={"submitted_by_user_id": "staff-paralegal-001", "submission_reference": "E2E-SUB-0001", "notes": "Filed during e2e test."},
    )
    assert_status(submit_response, 200)
    assert submit_response.json()["status"] == "submitted"

    close_response = client.post(
        f"/api/v1/cases/{case_id}/close",
        json={"closed_by_user_id": "staff-admin-001", "notes": "Closed after successful submission."},
    )
    assert_status(close_response, 200)
    assert close_response.json()["status"] == "closed"


def test_case_lifecycle_blocked_when_readiness_requirements_fail(e2e_client: tuple[TestClient, Any]) -> None:
    client, _ = e2e_client

    client_response = client.post(
        "/api/v1/clients",
        json={
            "first_name": "Blocked",
            "last_name": "Applicant",
            "email": "blocked.applicant@example.com",
            "phone": "+52-555-000-2222",
            "date_of_birth": "1990-01-01",
            "notes": "Created for blocked e2e scenario.",
        },
    )
    assert_status(client_response, 201)
    client_id = client_response.json()["id"]

    case_response = client.post(
        "/api/v1/cases",
        json={
            "client_id": client_id,
            "case_number": "CASE-E2E-0002",
            "case_type": "family-based",
            "status": "draft",
            "title": "Blocked readiness flow",
            "summary": "Should fail before ready_for_submission.",
        },
    )
    assert_status(case_response, 201)
    case_id = case_response.json()["id"]

    transition_response = client.post(
        f"/api/v1/cases/{case_id}/transition",
        json={"target_status": "ready_for_submission", "actor_reference": "staff-attorney-001", "notes": "Expect blocked."},
    )
    assert_status(transition_response, 400)
    body = transition_response.json()
    assert "blockers" in body["detail"], transition_response.text
    blocker_codes = {item["code"] for item in body["detail"]["blockers"]}
    assert "missing_required_documents" in blocker_codes, transition_response.text
    assert "missing_generated_forms" in blocker_codes, transition_response.text
    assert "missing_attorney_approval" in blocker_codes, transition_response.text

    approve_submission_response = client.post(
        f"/api/v1/cases/{case_id}/submission/approve",
        json={"approved_by_user_id": "staff-attorney-001", "notes": "Should stay blocked."},
    )
    assert_status(approve_submission_response, 400)
    assert "blockers" in approve_submission_response.json()["detail"], approve_submission_response.text
