from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal, configure_db_session
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.case_canonical_field import CaseCanonicalField
from app.models.client_portal import ClientPortalAccess
from app.models.case_packet import CasePacket
from app.models.case_submission import CaseSubmission
from app.models.client import Client
from app.models.document import Document
from app.models.document_checklist import CaseDocumentChecklistItem, DocumentChecklistTemplate, DocumentChecklistTemplateItem
from app.models.document_classification import DocumentClassification
from app.models.form import Form
from app.models.form_field_mapping import FormFieldMapping
from app.models.generated_form import GeneratedForm
from app.models.inconsistency import Inconsistency
from app.models.participant import Participant
from app.models.questionnaire import Questionnaire
from app.models.questionnaire_answer import QuestionnaireAnswer
from app.models.questionnaire_question import QuestionnaireQuestion
from app.models.questionnaire_response import QuestionnaireResponse
from app.models.questionnaire_section import QuestionnaireSection
from app.models.questionnaire_template import QuestionnaireTemplate
from app.models.review import Review
from app.services.roc_i751_defaults import ensure_roc_i751_defaults

SEED_CASE_NUMBERS = {
    "CASE-QA-0001",
    "CASE-QA-0002",
    "CASE-QA-0003",
    "CASE-QA-0004",
    "CASE-QA-0005",
    "CASE-QA-0006",
    "CASE-QA-0007",
}
SEED_CLIENT_EMAILS = {
    "ana.martinez.qa@example.com",
    "diego.ramirez.qa@example.com",
    "lucia.fernandez.qa@example.com",
    "carlos.lopez.qa@example.com",
    "mariana.torres.qa@example.com",
    "jorge.castillo.qa@example.com",
    "luz.sabogal.qa@example.com",
}
INTERNAL_USERS = [
    {"role": "admin", "name": "Valeria Admin", "email": "admin.qa@example.com", "reference": "staff-admin-001"},
    {"role": "attorney", "name": "Sofia Attorney", "email": "attorney.qa@example.com", "reference": "staff-attorney-001"},
    {"role": "paralegal", "name": "Mateo Paralegal", "email": "paralegal.qa@example.com", "reference": "staff-paralegal-001"},
    {"role": "qa", "name": "Renata QA", "email": "qa.reviewer@example.com", "reference": "staff-qa-001"},
]
CASE_TYPE_CATALOG = ["family-based", "employment-based", "humanitarian", "roc-i751"]
BASE_TIME = datetime(2026, 4, 2, 12, 0, tzinfo=UTC)
SEED_PORTAL_CREDENTIALS = {
    "case_7": {
        "token": "roc-demo-luz-i751-portal",
        "passcode": "ROC751",
        "instructions": (
            "Bienvenida al portal de ROC / I-751. Completa el cuestionario en espanol, "
            "sube los documentos solicitados y avisa a tu equipo legal si algun dato cambia."
        ),
    }
}


def seeded_at(days_ago: int, minutes: int = 0) -> datetime:
    return BASE_TIME - timedelta(days=days_ago, minutes=minutes)


def ensure_seed_file(storage_root: Path, case_number: str, stored_filename: str, contents: str) -> str:
    target = storage_root / case_number
    target.mkdir(parents=True, exist_ok=True)
    file_path = target / stored_filename
    file_path.write_text(contents, encoding="utf-8")
    return str(file_path)


def sha_for(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def file_size_for(contents: str) -> int:
    return len(contents.encode("utf-8"))


def build_form_payload(*, form_code: str, form_name: str, form_version: int, fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "form_code": form_code,
        "form_name": form_name,
        "form_version": form_version,
        "fields": fields,
    }


def build_packet_export(case_number: str, packet_version: int) -> dict[str, Any]:
    return {
        "artifact_type": "case_review_packet",
        "format": "json",
        "generated_at": BASE_TIME.isoformat(),
        "packet_version": packet_version,
        "bundle_path": f"/app/storage/packets/{case_number}/packet-v{packet_version}.json",
        "prefilled_forms_placeholder": {"ready": True, "available_templates": ["I-130", "I-140", "I-589", "I-751"]},
    }


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        await configure_db_session(session)
        existing_case = await session.scalar(select(Case).where(Case.case_number.in_(SEED_CASE_NUMBERS)))
        existing_client = await session.scalar(select(Client).where(Client.email.in_(SEED_CLIENT_EMAILS)))
        if existing_case is not None or existing_client is not None:
            print("Seed QA dataset already present. Reset the database or volumes to regenerate it.")
            return

        storage_root = Path(settings.document_storage_path)
        storage_root.mkdir(parents=True, exist_ok=True)

        clients = await seed_clients(session)
        cases = await seed_cases(session, clients)
        questionnaires = await seed_questionnaire_templates(session)
        forms = await seed_forms(session)
        await session.flush()

        await seed_participants(session, cases)
        await seed_case_questionnaires(session, cases, questionnaires)
        documents = await seed_documents(session, cases, storage_root)
        await seed_canonical_fields(session, cases, documents)
        await seed_case_checklists(session, cases)
        await seed_client_portal_accesses(session, cases)
        await seed_inconsistencies(session, cases)
        await seed_reviews(session, cases)
        await seed_packets(session, cases, documents)
        await seed_generated_forms(session, cases, forms)
        await seed_submissions(session, cases)
        await seed_audit_logs(session, cases)
        await session.commit()

        write_reference_files(storage_root.parent, cases)
        print("QA seed dataset created successfully.")


async def seed_clients(session: Any) -> dict[str, Client]:
    clients = {
        "ana": Client(
            first_name="Ana",
            last_name="Martinez",
            email="ana.martinez.qa@example.com",
            phone="+52-555-100-0001",
            date_of_birth=date(1992, 5, 14),
            notes="QA seed client for incomplete family-based case.",
        ),
        "diego": Client(
            first_name="Diego",
            last_name="Ramirez",
            email="diego.ramirez.qa@example.com",
            phone="+52-555-100-0002",
            date_of_birth=date(1988, 8, 22),
            notes="QA seed client in attorney review stage.",
        ),
        "lucia": Client(
            first_name="Lucia",
            last_name="Fernandez",
            email="lucia.fernandez.qa@example.com",
            phone="+52-555-100-0003",
            date_of_birth=date(1990, 2, 9),
            notes="QA seed client approved for submission.",
        ),
        "carlos": Client(
            first_name="Carlos",
            last_name="Lopez",
            email="carlos.lopez.qa@example.com",
            phone="+52-555-100-0004",
            date_of_birth=date(1985, 11, 4),
            notes="QA seed client with submitted employment-based filing.",
        ),
        "mariana": Client(
            first_name="Mariana",
            last_name="Torres",
            email="mariana.torres.qa@example.com",
            phone="+52-555-100-0005",
            date_of_birth=date(1994, 7, 30),
            notes="QA seed client with closed family-based filing.",
        ),
        "jorge": Client(
            first_name="Jorge",
            last_name="Castillo",
            email="jorge.castillo.qa@example.com",
            phone="+52-555-100-0006",
            date_of_birth=date(1991, 9, 19),
            notes="QA seed client with failed humanitarian submission.",
        ),
        "luz": Client(
            first_name="Luz Angela Maria",
            last_name="Sabogal Fuentes",
            email="luz.sabogal.qa@example.com",
            phone="+52-555-100-0007",
            date_of_birth=date(1986, 4, 2),
            notes="QA ROC / I-751 client seeded for the real interview, portal, and assisted form workflow.",
        ),
    }
    session.add_all(list(clients.values()))
    await session.flush()
    return clients


async def seed_cases(session: Any, clients: dict[str, Client]) -> dict[str, Case]:
    cases = {
        "case_1": Case(
            client_id=clients["ana"].id,
            case_number="CASE-QA-0001",
            case_type="family-based",
            status="draft",
            title="Family petition with missing evidence",
            summary="Incomplete family-based intake used to test blockers and missing data paths.",
        ),
        "case_2": Case(
            client_id=clients["diego"].id,
            case_number="CASE-QA-0002",
            case_type="family-based",
            status="attorney_review",
            title="Attorney review with open high inconsistency",
            summary="Family-based case with full docs and approved forms, but high inconsistency still open.",
        ),
        "case_3": Case(
            client_id=clients["lucia"].id,
            case_number="CASE-QA-0003",
            case_type="family-based",
            status="ready_for_submission",
            title="Ready family petition",
            summary="Case prepared for submission with attorney approval and approved generated forms.",
        ),
        "case_4": Case(
            client_id=clients["carlos"].id,
            case_number="CASE-QA-0004",
            case_type="employment-based",
            status="submitted",
            title="Submitted employment petition",
            summary="Employment-based case already submitted with reference for staff QA checks.",
        ),
        "case_5": Case(
            client_id=clients["mariana"].id,
            case_number="CASE-QA-0005",
            case_type="family-based",
            status="closed",
            title="Closed family-based case",
            summary="Completed case used to validate final state views and timeline behavior.",
        ),
        "case_6": Case(
            client_id=clients["jorge"].id,
            case_number="CASE-QA-0006",
            case_type="humanitarian",
            status="ready_for_submission",
            title="Humanitarian filing with failed submission",
            summary="Case ready on paper but with a failed submission attempt for QA regression flows.",
        ),
        "case_7": Case(
            client_id=clients["luz"].id,
            case_number="CASE-QA-0007",
            case_type="roc-i751",
            status="attorney_review",
            title="ROC I-751 joint filing demo",
            summary="Demo coherente del flujo ROC: entrevista, checklist, portal del cliente, documentos y borrador I-751.",
        ),
    }
    session.add_all(list(cases.values()))
    await session.flush()
    return cases


async def seed_participants(session: Any, cases: dict[str, Case]) -> None:
    participants = [
        Participant(case_id=cases["case_1"].id, role="petitioner", first_name="Ana", last_name="Martinez", email="ana.martinez.qa@example.com"),
        Participant(case_id=cases["case_1"].id, role="beneficiary", first_name="Luis", last_name="Martinez", email="luis.beneficiary.qa@example.com"),
        Participant(case_id=cases["case_2"].id, role="petitioner", first_name="Diego", last_name="Ramirez", email="diego.ramirez.qa@example.com"),
        Participant(case_id=cases["case_3"].id, role="petitioner", first_name="Lucia", last_name="Fernandez", email="lucia.fernandez.qa@example.com"),
        Participant(case_id=cases["case_4"].id, role="beneficiary", first_name="Carlos", last_name="Lopez", email="carlos.lopez.qa@example.com"),
        Participant(case_id=cases["case_5"].id, role="petitioner", first_name="Mariana", last_name="Torres", email="mariana.torres.qa@example.com"),
        Participant(case_id=cases["case_6"].id, role="applicant", first_name="Jorge", last_name="Castillo", email="jorge.castillo.qa@example.com"),
        Participant(case_id=cases["case_7"].id, role="conditional_resident", first_name="Luz Angela Maria", last_name="Sabogal Fuentes", email="luz.sabogal.qa@example.com"),
        Participant(case_id=cases["case_7"].id, role="spouse", first_name="Daniel", last_name="Fuentes", email="daniel.fuentes.qa@example.com"),
    ]
    session.add_all(participants)
    await session.flush()


async def seed_questionnaire_templates(session: Any) -> dict[str, dict[str, Any]]:
    family_template = QuestionnaireTemplate(
        case_type="family-based",
        title="Family-Based Intake Questionnaire",
        description="Initial intake for family-based immigration matters.",
        status="active",
        version=1,
    )
    employment_template = QuestionnaireTemplate(
        case_type="employment-based",
        title="Employment-Based Intake Questionnaire",
        description="Initial intake for employment filings.",
        status="active",
        version=1,
    )
    humanitarian_template = QuestionnaireTemplate(
        case_type="humanitarian",
        title="Humanitarian Intake Questionnaire",
        description="Initial intake for humanitarian and protection cases.",
        status="active",
        version=1,
    )
    session.add_all([family_template, employment_template, humanitarian_template])
    await session.flush()

    template_sections: dict[str, list[QuestionnaireSection]] = {
        "family-based": [
            QuestionnaireSection(template_id=family_template.id, title="Beneficiary Information", description="Identity and civil information.", display_order=1),
            QuestionnaireSection(template_id=family_template.id, title="Immigration History", description="Prior filings and travel history.", display_order=2),
        ],
        "employment-based": [
            QuestionnaireSection(template_id=employment_template.id, title="Employee Profile", description="Identity and role information.", display_order=1),
            QuestionnaireSection(template_id=employment_template.id, title="Employer Information", description="Petitioner and job offer details.", display_order=2),
        ],
        "humanitarian": [
            QuestionnaireSection(template_id=humanitarian_template.id, title="Applicant Profile", description="Core applicant information.", display_order=1),
            QuestionnaireSection(template_id=humanitarian_template.id, title="Protection Narrative", description="Case facts and humanitarian basis.", display_order=2),
        ],
    }
    for sections in template_sections.values():
        session.add_all(sections)
    await session.flush()

    questions = {
        "family-beneficiary-full-name": QuestionnaireQuestion(section_id=template_sections["family-based"][0].id, key="family_beneficiary_full_name", prompt="What is the beneficiary full legal name?", input_type="text", is_required=True, display_order=1, options=None, validation_rules=None),
        "family-beneficiary-dob": QuestionnaireQuestion(section_id=template_sections["family-based"][0].id, key="family_beneficiary_date_of_birth", prompt="What is the beneficiary date of birth?", input_type="date", is_required=True, display_order=2, options=None, validation_rules=None),
        "family-prior-filing": QuestionnaireQuestion(section_id=template_sections["family-based"][1].id, key="family_prior_filing", prompt="Has the beneficiary filed a prior immigration petition?", input_type="boolean", is_required=True, display_order=1, options=None, validation_rules=None),
        "family-visa-category": QuestionnaireQuestion(section_id=template_sections["family-based"][1].id, key="family_visa_category", prompt="Select the petition category.", input_type="single_select", is_required=True, display_order=2, options=[{"label": "Spouse of U.S. Citizen", "value": "ir1"}, {"label": "Parent of U.S. Citizen", "value": "ir5"}, {"label": "Sibling of U.S. Citizen", "value": "f4"}], validation_rules=None),
        "family-countries": QuestionnaireQuestion(section_id=template_sections["family-based"][1].id, key="family_supporting_countries", prompt="Select all countries where the beneficiary lived in the last five years.", input_type="multi_select", is_required=False, display_order=3, options=[{"label": "Mexico", "value": "mx"}, {"label": "United States", "value": "us"}, {"label": "Canada", "value": "ca"}], validation_rules=None),
        "family-metadata": QuestionnaireQuestion(section_id=template_sections["family-based"][1].id, key="family_case_metadata", prompt="Provide structured metadata relevant to the family-based filing.", input_type="json", is_required=False, display_order=4, options=None, validation_rules={"allowed_keys": ["interpreter_needed", "expedite_reason"]}),
        "employment-beneficiary-full-name": QuestionnaireQuestion(section_id=template_sections["employment-based"][0].id, key="employment_beneficiary_full_name", prompt="What is the beneficiary full legal name?", input_type="text", is_required=True, display_order=1, options=None, validation_rules=None),
        "employment-beneficiary-dob": QuestionnaireQuestion(section_id=template_sections["employment-based"][0].id, key="employment_beneficiary_date_of_birth", prompt="What is the beneficiary date of birth?", input_type="date", is_required=True, display_order=2, options=None, validation_rules=None),
        "employment-petition-type": QuestionnaireQuestion(section_id=template_sections["employment-based"][1].id, key="employment_petition_type", prompt="Select the employment petition type.", input_type="single_select", is_required=True, display_order=1, options=[{"label": "EB-2 NIW", "value": "eb2_niw"}, {"label": "EB-1A", "value": "eb1a"}, {"label": "PERM", "value": "perm"}], validation_rules=None),
        "employment-offer-active": QuestionnaireQuestion(section_id=template_sections["employment-based"][1].id, key="employment_offer_active", prompt="Is there an active job offer?", input_type="boolean", is_required=True, display_order=2, options=None, validation_rules=None),
        "employment-countries": QuestionnaireQuestion(section_id=template_sections["employment-based"][1].id, key="employment_supporting_countries", prompt="Select all countries where the beneficiary has worked in the last five years.", input_type="multi_select", is_required=False, display_order=3, options=[{"label": "Mexico", "value": "mx"}, {"label": "United States", "value": "us"}, {"label": "Germany", "value": "de"}], validation_rules=None),
        "employment-metadata": QuestionnaireQuestion(section_id=template_sections["employment-based"][1].id, key="employment_case_metadata", prompt="Provide structured metadata relevant to the employment filing.", input_type="json", is_required=False, display_order=4, options=None, validation_rules={"allowed_keys": ["premium_processing", "remote_role"]}),
        "humanitarian-applicant-full-name": QuestionnaireQuestion(section_id=template_sections["humanitarian"][0].id, key="humanitarian_applicant_full_name", prompt="What is the applicant full legal name?", input_type="text", is_required=True, display_order=1, options=None, validation_rules=None),
        "humanitarian-applicant-dob": QuestionnaireQuestion(section_id=template_sections["humanitarian"][0].id, key="humanitarian_applicant_date_of_birth", prompt="What is the applicant date of birth?", input_type="date", is_required=True, display_order=2, options=None, validation_rules=None),
        "humanitarian-prior-entry": QuestionnaireQuestion(section_id=template_sections["humanitarian"][1].id, key="humanitarian_prior_entry", prompt="Has the applicant entered the United States before?", input_type="boolean", is_required=True, display_order=1, options=None, validation_rules=None),
        "humanitarian-program": QuestionnaireQuestion(section_id=template_sections["humanitarian"][1].id, key="humanitarian_program", prompt="Select the humanitarian program.", input_type="single_select", is_required=True, display_order=2, options=[{"label": "Asylum", "value": "asylum"}, {"label": "TPS", "value": "tps"}, {"label": "U Visa", "value": "uvisa"}], validation_rules=None),
        "humanitarian-countries": QuestionnaireQuestion(section_id=template_sections["humanitarian"][1].id, key="humanitarian_relevant_countries", prompt="Select all countries related to the protection claim.", input_type="multi_select", is_required=False, display_order=3, options=[{"label": "Mexico", "value": "mx"}, {"label": "Honduras", "value": "hn"}, {"label": "Guatemala", "value": "gt"}], validation_rules=None),
        "humanitarian-metadata": QuestionnaireQuestion(section_id=template_sections["humanitarian"][1].id, key="humanitarian_case_metadata", prompt="Provide structured metadata relevant to the humanitarian filing.", input_type="json", is_required=False, display_order=4, options=None, validation_rules={"allowed_keys": ["detained", "interpreter_needed"]}),
    }
    session.add_all(list(questions.values()))
    await session.flush()

    return {
        "templates": {"family-based": family_template, "employment-based": employment_template, "humanitarian": humanitarian_template},
        "questions": questions,
    }


async def seed_case_questionnaires(session: Any, cases: dict[str, Case], questionnaires: dict[str, dict[str, Any]]) -> None:
    case_answers: dict[str, list[dict[str, Any]]] = {
        "case_1": [{"question_key": "family-beneficiary-full-name", "text": "Luis Martinez"}, {"question_key": "family-prior-filing", "boolean": False}, {"question_key": "family-visa-category", "choice": "ir1"}, {"question_key": "family-countries", "choices": ["mx"]}, {"question_key": "family-metadata", "json": {"interpreter_needed": True, "expedite_reason": "medical hardship"}}],
        "case_2": [{"question_key": "family-beneficiary-full-name", "text": "Diego Ramirez"}, {"question_key": "family-beneficiary-dob", "date": date(1988, 8, 22)}, {"question_key": "family-prior-filing", "boolean": True}, {"question_key": "family-visa-category", "choice": "ir5"}, {"question_key": "family-countries", "choices": ["mx", "us"]}, {"question_key": "family-metadata", "json": {"interpreter_needed": False, "expedite_reason": ""}}],
        "case_3": [{"question_key": "family-beneficiary-full-name", "text": "Lucia Fernandez"}, {"question_key": "family-beneficiary-dob", "date": date(1990, 2, 9)}, {"question_key": "family-prior-filing", "boolean": False}, {"question_key": "family-visa-category", "choice": "ir1"}, {"question_key": "family-countries", "choices": ["mx", "ca"]}, {"question_key": "family-metadata", "json": {"interpreter_needed": False, "expedite_reason": "age-out risk"}}],
        "case_4": [{"question_key": "employment-beneficiary-full-name", "text": "Carlos Lopez"}, {"question_key": "employment-beneficiary-dob", "date": date(1985, 11, 4)}, {"question_key": "employment-petition-type", "choice": "eb2_niw"}, {"question_key": "employment-offer-active", "boolean": True}, {"question_key": "employment-countries", "choices": ["mx", "us", "de"]}, {"question_key": "employment-metadata", "json": {"premium_processing": True, "remote_role": False}}],
        "case_5": [{"question_key": "family-beneficiary-full-name", "text": "Mariana Torres"}, {"question_key": "family-beneficiary-dob", "date": date(1994, 7, 30)}, {"question_key": "family-prior-filing", "boolean": False}, {"question_key": "family-visa-category", "choice": "ir1"}, {"question_key": "family-countries", "choices": ["mx", "us"]}, {"question_key": "family-metadata", "json": {"interpreter_needed": False, "expedite_reason": ""}}],
        "case_6": [{"question_key": "humanitarian-applicant-full-name", "text": "Jorge Castillo"}, {"question_key": "humanitarian-applicant-dob", "date": date(1991, 9, 19)}, {"question_key": "humanitarian-prior-entry", "boolean": True}, {"question_key": "humanitarian-program", "choice": "asylum"}, {"question_key": "humanitarian-countries", "choices": ["hn", "gt"]}, {"question_key": "humanitarian-metadata", "json": {"detained": False, "interpreter_needed": True}}],
        "case_7": [
            {"question_key": "last_name", "text": "Sabogal Fuentes"},
            {"question_key": "first_name", "text": "Luz Angela Maria"},
            {"question_key": "middle_name", "text": ""},
            {"question_key": "other_names_used", "text": "Luz Sabogal"},
            {"question_key": "date_of_birth", "date": date(1986, 4, 2)},
            {"question_key": "country_of_birth", "text": "Colombia"},
            {"question_key": "country_of_citizenship", "text": "Colombia"},
            {"question_key": "alien_registration_number", "text": "A123456789"},
            {"question_key": "ssn", "text": "555-55-1207"},
            {"question_key": "uscis_elis_account_number", "text": "ELIS123456"},
            {"question_key": "marital_status", "choice": "married"},
            {"question_key": "marriage_date", "date": date(2021, 6, 18)},
            {"question_key": "marriage_place", "text": "San Antonio, Texas"},
            {"question_key": "conditional_residence_expires_on", "date": date(2026, 6, 14)},
            {"question_key": "mailing_address", "text": "742 Evergreen Terrace Apt 3B, San Antonio, TX 78207"},
            {"question_key": "physical_address_same_as_mailing", "choice": "yes"},
            {"question_key": "in_removal_proceedings", "choice": "no"},
            {"question_key": "third_party_fee_paid", "choice": "no"},
            {"question_key": "arrest_history", "choice": "no"},
            {"question_key": "different_marriage_basis", "choice": "no"},
            {"question_key": "prior_addresses_since_residence", "json": [{"from": "2024-06-15", "to": "Present", "street": "742 Evergreen Terrace", "unit": "Apt 3B", "city": "San Antonio", "county": "Bexar", "state": "TX", "zip": "78207"}]},
            {"question_key": "government_overseas_service", "choice": "no"},
            {"question_key": "ethnicity", "choice": "hispanic_or_latino"},
            {"question_key": "race", "text": "White"},
            {"question_key": "height_feet", "text": "5"},
            {"question_key": "height_inches", "text": "4"},
            {"question_key": "weight_lbs", "text": "132"},
            {"question_key": "eye_color", "choice": "brown"},
            {"question_key": "hair_color", "choice": "black"},
            {"question_key": "joint_filing_party", "choice": "spouse"},
            {"question_key": "spouse_relationship", "choice": "spouse"},
            {"question_key": "spouse_last_name", "text": "Fuentes"},
            {"question_key": "spouse_first_name", "text": "Daniel"},
            {"question_key": "spouse_middle_name", "text": "Alejandro"},
            {"question_key": "spouse_date_of_birth", "date": date(1984, 11, 12)},
            {"question_key": "spouse_ssn", "text": "555-55-8910"},
            {"question_key": "spouse_physical_address", "text": "742 Evergreen Terrace Apt 3B, San Antonio, TX 78207"},
            {"question_key": "children", "json": [{"full_name": "Sofia Fuentes Sabogal", "date_of_birth": "2023-02-17", "a_number": "", "living_with_you": "yes", "applying_with_you": "no", "address": "742 Evergreen Terrace Apt 3B, San Antonio, TX 78207"}]},
            {"question_key": "accommodation_requested_self", "choice": "no"},
            {"question_key": "accommodation_requested_spouse", "choice": "no"},
            {"question_key": "accommodation_requested_children", "choice": "no"},
            {"question_key": "petitioner_can_read_english", "choice": "yes"},
            {"question_key": "beneficiary_can_read_english", "choice": "yes"},
            {"question_key": "additional_information", "text": "Joint filing with strong commingled evidence, one shared child, and continuous cohabitation."},
        ],
    }

    question_map: dict[str, QuestionnaireQuestion] = dict(questionnaires["questions"])
    roc_template = await session.scalar(
        select(QuestionnaireTemplate)
        .where(QuestionnaireTemplate.case_type == "roc-i751", QuestionnaireTemplate.status == "active")
        .order_by(QuestionnaireTemplate.version.desc())
    )
    if roc_template is not None:
        roc_questions = await session.scalars(
            select(QuestionnaireQuestion)
            .join(QuestionnaireSection, QuestionnaireQuestion.section_id == QuestionnaireSection.id)
            .where(QuestionnaireSection.template_id == roc_template.id)
        )
        for question in roc_questions:
            question_map[question.key] = question
    template_titles = {"family-based": "Family-Based Intake Questionnaire", "employment-based": "Employment-Based Intake Questionnaire", "humanitarian": "Humanitarian Intake Questionnaire", "roc-i751": "Cuestionario ROC / I-751"}

    for case_key, case in cases.items():
        questionnaire = Questionnaire(case_id=case.id, title=template_titles[case.case_type], status="submitted" if case_key != "case_1" else "draft", version=1, submitted_at=seeded_at(15 if case_key == "case_1" else 10))
        session.add(questionnaire)
        await session.flush()

        for answer_payload in case_answers[case_key]:
            question = question_map[answer_payload["question_key"]]
            answer_text = answer_payload.get("text")
            answer_date = answer_payload.get("date")
            answer_boolean = answer_payload.get("boolean")
            answer_choice = answer_payload.get("choice")
            answer_choices = answer_payload.get("choices")
            answer_json = answer_payload.get("json")
            response = QuestionnaireResponse(
                questionnaire_id=questionnaire.id,
                question_key=question.key,
                question_text=question.prompt,
                answer_text=(answer_text or (answer_date.isoformat() if answer_date is not None else None) or (str(answer_boolean).lower() if answer_boolean is not None else None) or answer_choice),
                answer_json=answer_json or answer_choices,
            )
            answer = QuestionnaireAnswer(case_id=case.id, question_id=question.id, answer_text=answer_text, answer_date=answer_date, answer_boolean=answer_boolean, answer_choice=answer_choice, answer_choices=answer_choices, answer_json=answer_json)
            session.add_all([response, answer])
        await session.flush()


async def seed_forms(session: Any) -> dict[str, Form]:
    family_form = Form(case_type_id="family-based", form_code="I-130", form_name="Petition for Alien Relative", version=1, is_active=True)
    employment_form = Form(case_type_id="employment-based", form_code="I-140", form_name="Immigrant Petition for Alien Worker", version=1, is_active=True)
    humanitarian_form = Form(case_type_id="humanitarian", form_code="I-589", form_name="Application for Asylum and for Withholding of Removal", version=1, is_active=True)
    session.add_all([family_form, employment_form, humanitarian_form])
    await session.flush()

    mappings = [
        FormFieldMapping(form_id=family_form.id, form_field_key="beneficiary.full_name", canonical_field_key="beneficiary.full_name", transform_rule_json={"uppercase": True}, required=True),
        FormFieldMapping(form_id=family_form.id, form_field_key="beneficiary.date_of_birth", canonical_field_key="beneficiary.date_of_birth", transform_rule_json=None, required=True),
        FormFieldMapping(form_id=family_form.id, form_field_key="petition.category", canonical_field_key="petition.category", transform_rule_json=None, required=True),
        FormFieldMapping(form_id=employment_form.id, form_field_key="beneficiary.full_name", canonical_field_key="beneficiary.full_name", transform_rule_json=None, required=True),
        FormFieldMapping(form_id=employment_form.id, form_field_key="job.offer_active", canonical_field_key="job.offer_active", transform_rule_json={"boolean_to": {"true": "yes", "false": "no"}}, required=True),
        FormFieldMapping(form_id=employment_form.id, form_field_key="petition.type", canonical_field_key="petition.category", transform_rule_json=None, required=True),
        FormFieldMapping(form_id=humanitarian_form.id, form_field_key="applicant.full_name", canonical_field_key="beneficiary.full_name", transform_rule_json=None, required=True),
        FormFieldMapping(form_id=humanitarian_form.id, form_field_key="program.selected", canonical_field_key="petition.category", transform_rule_json=None, required=True),
        FormFieldMapping(form_id=humanitarian_form.id, form_field_key="narrative.summary", canonical_field_key="humanitarian.summary", transform_rule_json={"default_value": "Pending narrative review"}, required=False),
    ]
    session.add_all(mappings)
    await session.flush()
    await ensure_roc_i751_defaults(session, "roc-i751")
    roc_form = await session.scalar(
        select(Form).where(Form.case_type_id == "roc-i751", Form.form_code == "I-751", Form.is_active.is_(True))
    )
    return {"family-based": family_form, "employment-based": employment_form, "humanitarian": humanitarian_form, "roc-i751": roc_form}


async def seed_documents(session: Any, cases: dict[str, Case], storage_root: Path) -> dict[str, dict[str, Document]]:
    docs: dict[str, dict[str, Document]] = {key: {} for key in cases}

    async def add_document(
        *,
        case_key: str,
        uploaded_by: str,
        document_type: str,
        original_filename: str,
        stored_filename: str,
        mime_type: str,
        contents: str,
        document_status: str,
        processing_status: str,
        classification_label: str,
        classification_source: str,
        classification_confidence_score: float,
        version_number: int,
        uploaded_at: datetime,
        extracted_text: str | None = None,
        extracted_fields: dict[str, Any] | list[Any] | None = None,
        extracted_metadata: dict[str, Any] | None = None,
        replacement_notes: str | None = None,
        previous_version: Document | None = None,
    ) -> Document:
        case = cases[case_key]
        file_path = ensure_seed_file(storage_root, case.case_number, stored_filename, contents)
        document = Document(
            case_id=case.id,
            uploaded_by_user_id=uploaded_by,
            document_type=document_type,
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_backend="local",
            storage_key=file_path,
            mime_type=mime_type,
            size_bytes=file_size_for(contents),
            sha256_hash=sha_for(f"{case.case_number}-{stored_filename}"),
            document_status=document_status,
            processing_status=processing_status,
            classification_label=classification_label,
            classification_source=classification_source,
            classification_confidence_score=classification_confidence_score,
            file_metadata={"seeded": True, "original_filename": original_filename, "size_bytes": file_size_for(contents)},
            extracted_text=extracted_text,
            extracted_fields=extracted_fields,
            extracted_metadata=extracted_metadata or {"seeded": True},
            version_number=version_number,
            is_current=previous_version is None,
            previous_version_id=previous_version.id if previous_version is not None else None,
            root_document_id=previous_version.root_document_id if previous_version is not None else None,
            replacement_notes=replacement_notes,
            uploaded_at=uploaded_at,
        )
        session.add(document)
        await session.flush()
        if previous_version is None:
            document.root_document_id = document.id
        else:
            previous_version.is_current = False
        classification = DocumentClassification(
            case_id=case.id,
            document_id=document.id,
            version_number=document.version_number,
            predicted_type=classification_label,
            confidence_score=classification_confidence_score,
            classification_source=classification_source,
            classification_method="seed_rules",
            is_override=classification_source == "manual",
            is_active=True,
            reviewed_by_user_id=uploaded_by if classification_source == "manual" else None,
            review_notes="Seeded document classification.",
            evidence_payload={"seeded": True, "storage_key": file_path},
        )
        session.add(classification)
        await session.flush()
        docs[case_key][stored_filename] = document
        return document

    await add_document(case_key="case_1", uploaded_by="staff-paralegal-001", document_type="passport", original_filename="ana_passport_scan.pdf", stored_filename="ana-passport-v1.pdf", mime_type="application/pdf", contents="Passport scan for Luis Martinez. Date of birth 1992-05-14.", document_status="processed", processing_status="processed", classification_label="passport", classification_source="automatic", classification_confidence_score=0.99, version_number=1, uploaded_at=seeded_at(18), extracted_text="Passport issued to Luis Martinez. DOB 1992-05-14. Country: Mexico.", extracted_fields={"document_number": "MX1234567", "date_of_birth": "1992-05-14"}, extracted_metadata={"pages": 1, "language": "spa"})
    await add_document(case_key="case_1", uploaded_by="staff-paralegal-001", document_type="evidence", original_filename="relationship_photos.zip", stored_filename="relationship-photos-v1.pdf", mime_type="application/pdf", contents="Evidence index with captions and travel tickets.", document_status="manual_review", processing_status="failed", classification_label="evidence", classification_source="automatic", classification_confidence_score=0.62, version_number=1, uploaded_at=seeded_at(17), extracted_text=None, extracted_fields=None, extracted_metadata={"manual_review_reason": "unsupported scan quality"})

    passport_v1 = await add_document(case_key="case_2", uploaded_by="staff-paralegal-001", document_type="passport", original_filename="diego_passport_old.pdf", stored_filename="diego-passport-v1.pdf", mime_type="application/pdf", contents="Old passport copy for Diego Ramirez.", document_status="archived", processing_status="processed", classification_label="passport", classification_source="manual", classification_confidence_score=1.0, version_number=1, uploaded_at=seeded_at(40), extracted_text="Old passport issued to Diego Ramirez.", extracted_fields={"document_number": "MX7654321"}, extracted_metadata={"pages": 1})
    await add_document(case_key="case_2", uploaded_by="staff-paralegal-001", document_type="passport", original_filename="diego_passport_new.pdf", stored_filename="diego-passport-v2.pdf", mime_type="application/pdf", contents="Updated passport copy for Diego Ramirez. DOB 1988-08-20.", document_status="processed", processing_status="processed", classification_label="passport", classification_source="manual", classification_confidence_score=1.0, version_number=2, uploaded_at=seeded_at(14), extracted_text="Passport issued to Diego Ramirez. DOB 1988-08-20.", extracted_fields={"document_number": "MX7654321", "date_of_birth": "1988-08-20"}, extracted_metadata={"pages": 2}, replacement_notes="Renewed passport uploaded.", previous_version=passport_v1)
    await add_document(case_key="case_2", uploaded_by="staff-paralegal-001", document_type="birth_certificate", original_filename="diego_birth_certificate.pdf", stored_filename="diego-birth-certificate-v1.pdf", mime_type="application/pdf", contents="Birth certificate for Diego Ramirez. DOB 1988-08-22.", document_status="processed", processing_status="processed", classification_label="birth_certificate", classification_source="automatic", classification_confidence_score=0.97, version_number=1, uploaded_at=seeded_at(13), extracted_text="Birth certificate: Diego Ramirez. Date of birth 1988-08-22.", extracted_fields={"date_of_birth": "1988-08-22"}, extracted_metadata={"pages": 1})
    await add_document(case_key="case_2", uploaded_by="staff-paralegal-001", document_type="marriage_certificate", original_filename="diego_marriage_certificate.pdf", stored_filename="diego-marriage-certificate-v1.pdf", mime_type="application/pdf", contents="Marriage certificate for Diego Ramirez and spouse.", document_status="processed", processing_status="processed", classification_label="marriage_certificate", classification_source="automatic", classification_confidence_score=0.95, version_number=1, uploaded_at=seeded_at(12), extracted_text="Marriage certificate for Diego Ramirez.", extracted_fields={"spouse_name": "Laura Ramirez"}, extracted_metadata={"pages": 1})
    await add_document(case_key="case_2", uploaded_by="staff-paralegal-001", document_type="evidence", original_filename="diego_relationship_evidence.pdf", stored_filename="diego-evidence-v1.pdf", mime_type="application/pdf", contents="Relationship evidence package with travel and lease records.", document_status="processed", processing_status="processed", classification_label="evidence", classification_source="automatic", classification_confidence_score=0.89, version_number=1, uploaded_at=seeded_at(11), extracted_text="Evidence package index with 12 exhibits.", extracted_fields={"exhibits": 12}, extracted_metadata={"pages": 8})

    for case_key, person_name, dob in [("case_3", "Lucia Fernandez", "1990-02-09"), ("case_5", "Mariana Torres", "1994-07-30")]:
        prefix = person_name.split()[0].lower()
        await add_document(case_key=case_key, uploaded_by="staff-paralegal-001", document_type="passport", original_filename=f"{prefix}_passport.pdf", stored_filename=f"{prefix}-passport-v1.pdf", mime_type="application/pdf", contents=f"Passport for {person_name}. DOB {dob}.", document_status="processed", processing_status="processed", classification_label="passport", classification_source="automatic", classification_confidence_score=0.99, version_number=1, uploaded_at=seeded_at(9 if case_key == "case_3" else 120), extracted_text=f"Passport issued to {person_name}. DOB {dob}.", extracted_fields={"date_of_birth": dob}, extracted_metadata={"pages": 1})
        await add_document(case_key=case_key, uploaded_by="staff-paralegal-001", document_type="birth_certificate", original_filename=f"{prefix}_birth_certificate.pdf", stored_filename=f"{prefix}-birth-certificate-v1.pdf", mime_type="application/pdf", contents=f"Birth certificate for {person_name}. DOB {dob}.", document_status="processed", processing_status="processed", classification_label="birth_certificate", classification_source="automatic", classification_confidence_score=0.97, version_number=1, uploaded_at=seeded_at(8 if case_key == "case_3" else 118), extracted_text=f"Birth certificate for {person_name}. DOB {dob}.", extracted_fields={"date_of_birth": dob}, extracted_metadata={"pages": 1})
        await add_document(case_key=case_key, uploaded_by="staff-paralegal-001", document_type="marriage_certificate", original_filename=f"{prefix}_marriage_certificate.pdf", stored_filename=f"{prefix}-marriage-certificate-v1.pdf", mime_type="application/pdf", contents=f"Marriage certificate packet for {person_name}.", document_status="processed", processing_status="processed", classification_label="marriage_certificate", classification_source="automatic", classification_confidence_score=0.95, version_number=1, uploaded_at=seeded_at(7 if case_key == "case_3" else 117), extracted_text=f"Marriage certificate for {person_name}.", extracted_fields={"marital_status": "married"}, extracted_metadata={"pages": 1})
        await add_document(case_key=case_key, uploaded_by="staff-paralegal-001", document_type="evidence", original_filename=f"{prefix}_evidence_bundle.pdf", stored_filename=f"{prefix}-evidence-v1.pdf", mime_type="application/pdf", contents=f"Evidentiary packet for {person_name}.", document_status="processed", processing_status="processed", classification_label="evidence", classification_source="automatic", classification_confidence_score=0.88, version_number=1, uploaded_at=seeded_at(6 if case_key == "case_3" else 116), extracted_text="Evidence packet with supporting exhibits.", extracted_fields={"exhibits": 10}, extracted_metadata={"pages": 10})

    await add_document(case_key="case_4", uploaded_by="staff-paralegal-001", document_type="passport", original_filename="carlos_passport.pdf", stored_filename="carlos-passport-v1.pdf", mime_type="application/pdf", contents="Passport for Carlos Lopez. DOB 1985-11-04.", document_status="processed", processing_status="processed", classification_label="passport", classification_source="automatic", classification_confidence_score=0.98, version_number=1, uploaded_at=seeded_at(30), extracted_text="Passport for Carlos Lopez. DOB 1985-11-04.", extracted_fields={"date_of_birth": "1985-11-04"}, extracted_metadata={"pages": 1})
    await add_document(case_key="case_4", uploaded_by="staff-paralegal-001", document_type="evidence", original_filename="carlos_niw_evidence.pdf", stored_filename="carlos-evidence-v1.pdf", mime_type="application/pdf", contents="Evidence of national interest work and publications.", document_status="processed", processing_status="processed", classification_label="evidence", classification_source="automatic", classification_confidence_score=0.91, version_number=1, uploaded_at=seeded_at(28), extracted_text="National interest evidence with publications and recommendation letters.", extracted_fields={"publication_count": 6}, extracted_metadata={"pages": 14})

    await add_document(case_key="case_6", uploaded_by="staff-paralegal-001", document_type="passport", original_filename="jorge_passport.pdf", stored_filename="jorge-passport-v1.pdf", mime_type="application/pdf", contents="Passport for Jorge Castillo. DOB 1991-09-19.", document_status="processed", processing_status="processed", classification_label="passport", classification_source="automatic", classification_confidence_score=0.98, version_number=1, uploaded_at=seeded_at(20), extracted_text="Passport for Jorge Castillo. DOB 1991-09-19.", extracted_fields={"date_of_birth": "1991-09-19"}, extracted_metadata={"pages": 1})
    await add_document(case_key="case_6", uploaded_by="staff-paralegal-001", document_type="evidence", original_filename="jorge_humanitarian_evidence.pdf", stored_filename="jorge-evidence-v1.pdf", mime_type="application/pdf", contents="Humanitarian evidence packet with declarations.", document_status="processed", processing_status="processed", classification_label="evidence", classification_source="automatic", classification_confidence_score=0.87, version_number=1, uploaded_at=seeded_at(19), extracted_text="Protection claim evidence including declaration and country conditions.", extracted_fields={"declarations": 3}, extracted_metadata={"pages": 12})

    await add_document(case_key="case_7", uploaded_by="staff-paralegal-001", document_type="conditional_resident_card", original_filename="luz_green_card.pdf", stored_filename="luz-green-card-v1.pdf", mime_type="application/pdf", contents="Permanent resident card for Luz Angela Maria Sabogal Fuentes. A-Number A123456789. Expires 2026-06-14.", document_status="processed", processing_status="processed", classification_label="conditional_resident_card", classification_source="automatic", classification_confidence_score=0.99, version_number=1, uploaded_at=seeded_at(9), extracted_text="Permanent resident card. Luz Angela Maria Sabogal Fuentes. A123456789. Expires 2026-06-14.", extracted_fields={"alien_registration_number": "A123456789", "conditional_residence_expires_on": "2026-06-14", "date_of_birth": "1986-04-02"}, extracted_metadata={"pages": 2})
    await add_document(case_key="case_7", uploaded_by="staff-paralegal-001", document_type="marriage_certificate", original_filename="luz_marriage_certificate.pdf", stored_filename="luz-marriage-certificate-v1.pdf", mime_type="application/pdf", contents="Marriage certificate for Luz Angela Maria Sabogal Fuentes and Daniel Alejandro Fuentes. Married on 2021-06-18 in San Antonio, Texas.", document_status="processed", processing_status="processed", classification_label="marriage_certificate", classification_source="automatic", classification_confidence_score=0.98, version_number=1, uploaded_at=seeded_at(8), extracted_text="Marriage certificate. Luz Angela Maria Sabogal Fuentes and Daniel Alejandro Fuentes. 2021-06-18. San Antonio, Texas.", extracted_fields={"marriage_date": "2021-06-18", "marriage_place": "San Antonio, Texas", "spouse_first_name": "Daniel", "spouse_last_name": "Fuentes"}, extracted_metadata={"pages": 1})
    await add_document(case_key="case_7", uploaded_by="staff-paralegal-001", document_type="joint_tax_returns", original_filename="luz_joint_tax_returns_2024.pdf", stored_filename="luz-joint-tax-returns-v1.pdf", mime_type="application/pdf", contents="Joint tax return for Luz and Daniel Fuentes for tax year 2024.", document_status="processed", processing_status="processed", classification_label="joint_tax_returns", classification_source="automatic", classification_confidence_score=0.93, version_number=1, uploaded_at=seeded_at(7), extracted_text="Joint tax return filed married filing jointly for 2024.", extracted_fields={"filing_status": "married_filing_jointly", "tax_year": "2024"}, extracted_metadata={"pages": 24})
    await add_document(case_key="case_7", uploaded_by="client-portal:roc-demo", document_type="joint_bank_statements", original_filename="luz_joint_bank_statements.pdf", stored_filename="luz-joint-bank-statements-v1.pdf", mime_type="application/pdf", contents="Joint bank statements for Luz and Daniel covering six months.", document_status="received_from_client", processing_status="processed", classification_label="joint_bank_statements", classification_source="client_portal", classification_confidence_score=0.95, version_number=1, uploaded_at=seeded_at(5), extracted_text="Joint account statements for six consecutive months.", extracted_fields={"statement_months": 6}, extracted_metadata={"pages": 12})
    await add_document(case_key="case_7", uploaded_by="client-portal:roc-demo", document_type="children_birth_certificates", original_filename="sofia_birth_certificate.pdf", stored_filename="sofia-birth-certificate-v1.pdf", mime_type="application/pdf", contents="Birth certificate for Sofia Fuentes Sabogal. Born 2023-02-17 to Luz Angela Maria Sabogal Fuentes and Daniel Alejandro Fuentes.", document_status="received_from_client", processing_status="processed", classification_label="children_birth_certificates", classification_source="client_portal", classification_confidence_score=0.96, version_number=1, uploaded_at=seeded_at(4), extracted_text="Birth certificate for Sofia Fuentes Sabogal. DOB 2023-02-17.", extracted_fields={"child_name": "Sofia Fuentes Sabogal", "child_date_of_birth": "2023-02-17"}, extracted_metadata={"pages": 1})
    await add_document(case_key="case_7", uploaded_by="client-portal:roc-demo", document_type="relationship_photos", original_filename="luz_relationship_photos.pdf", stored_filename="luz-relationship-photos-v1.pdf", mime_type="application/pdf", contents="Ten captioned family photos for Luz and Daniel.", document_status="received_from_client", processing_status="processed", classification_label="relationship_photos", classification_source="client_portal", classification_confidence_score=0.92, version_number=1, uploaded_at=seeded_at(3), extracted_text="Captioned family photo packet with ten images.", extracted_fields={"photo_count": 10}, extracted_metadata={"pages": 10})

    await session.flush()
    return docs


async def seed_canonical_fields(session: Any, cases: dict[str, Case], documents: dict[str, dict[str, Document]]) -> None:
    fields: list[CaseCanonicalField] = []
    for case_key, case in cases.items():
        current_documents = [document for document in documents[case_key].values() if document.is_current]
        source_document_id = current_documents[0].id if current_documents else None
        if case.case_type == "family-based":
            full_name = {"case_1": "Luis Martinez", "case_2": "Diego Ramirez", "case_3": "Lucia Fernandez", "case_5": "Mariana Torres"}[case_key]
            date_of_birth = {"case_2": "1988-08-22", "case_3": "1990-02-09", "case_5": "1994-07-30"}.get(case_key)
            petition_category = {"case_1": "ir1", "case_2": "ir5", "case_3": "ir1", "case_5": "ir1"}[case_key]
            fields.extend([
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="beneficiary.full_name", field_value=full_name, confidence_score=0.9900, source_priority=100, status="approved" if case_key in {"case_3", "case_5"} else "confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="petition.category", field_value=petition_category, confidence_score=0.9100, source_priority=90, status="confirmed"),
            ])
            if date_of_birth is not None:
                fields.append(CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="beneficiary.date_of_birth", field_value=date_of_birth, confidence_score=0.9600, source_priority=95, status="approved" if case_key in {"case_3", "case_5"} else "confirmed"))
        if case.case_type == "employment-based":
            fields.extend([
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="beneficiary.full_name", field_value="Carlos Lopez", confidence_score=0.9900, source_priority=100, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="beneficiary.date_of_birth", field_value="1985-11-04", confidence_score=0.9700, source_priority=95, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="petition.category", field_value="eb2_niw", confidence_score=0.9400, source_priority=90, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="job.offer_active", field_value=True, confidence_score=0.8800, source_priority=85, status="confirmed"),
            ])
        if case.case_type == "humanitarian":
            fields.extend([
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="beneficiary.full_name", field_value="Jorge Castillo", confidence_score=0.9900, source_priority=100, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="beneficiary.date_of_birth", field_value="1991-09-19", confidence_score=0.9700, source_priority=95, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="petition.category", field_value="asylum", confidence_score=0.9300, source_priority=90, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="humanitarian.summary", field_value="Fear-based claim supported by declarations and country conditions.", confidence_score=0.8100, source_priority=70, status="suggested"),
            ])
        if case.case_type == "roc-i751":
            fields.extend([
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="last_name", field_value="Sabogal Fuentes", confidence_score=0.9900, source_priority=100, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="first_name", field_value="Luz Angela Maria", confidence_score=0.9900, source_priority=99, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="middle_name", field_value="", confidence_score=0.7000, source_priority=40, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="other_names_used", field_value="Luz Sabogal", confidence_score=0.8200, source_priority=60, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="date_of_birth", field_value="1986-04-02", confidence_score=0.9800, source_priority=98, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="country_of_birth", field_value="Colombia", confidence_score=0.9300, source_priority=90, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="country_of_citizenship", field_value="Colombia", confidence_score=0.9300, source_priority=90, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="alien_registration_number", field_value="A123456789", confidence_score=0.9900, source_priority=100, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="ssn", field_value="555-55-1207", confidence_score=0.8800, source_priority=80, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="uscis_elis_account_number", field_value="ELIS123456", confidence_score=0.7600, source_priority=50, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="marital_status", field_value="married", confidence_score=0.9500, source_priority=94, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="marriage_date", field_value="2021-06-18", confidence_score=0.9800, source_priority=98, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="marriage_place", field_value="San Antonio, Texas", confidence_score=0.9600, source_priority=97, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="conditional_residence_expires_on", field_value="2026-06-14", confidence_score=0.9800, source_priority=97, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="mailing_address", field_value="742 Evergreen Terrace Apt 3B, San Antonio, TX 78207", confidence_score=0.9300, source_priority=90, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="physical_address", field_value="742 Evergreen Terrace Apt 3B, San Antonio, TX 78207", confidence_score=0.9300, source_priority=90, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="in_removal_proceedings", field_value="no", confidence_score=0.9100, source_priority=80, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="arrest_history", field_value="no", confidence_score=0.9100, source_priority=80, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="joint_filing_party", field_value="spouse", confidence_score=0.9400, source_priority=90, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="spouse_relationship", field_value="spouse", confidence_score=0.9400, source_priority=90, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="spouse_last_name", field_value="Fuentes", confidence_score=0.9800, source_priority=97, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="spouse_first_name", field_value="Daniel", confidence_score=0.9800, source_priority=97, status="approved"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="spouse_middle_name", field_value="Alejandro", confidence_score=0.9000, source_priority=70, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="spouse_date_of_birth", field_value="1984-11-12", confidence_score=0.8700, source_priority=65, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="spouse_ssn", field_value="555-55-8910", confidence_score=0.7600, source_priority=50, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="spouse_physical_address", field_value="742 Evergreen Terrace Apt 3B, San Antonio, TX 78207", confidence_score=0.9300, source_priority=90, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="children", field_value=[{"full_name": "Sofia Fuentes Sabogal", "date_of_birth": "2023-02-17", "a_number": "", "living_with_you": "yes", "applying_with_you": "no", "address": "742 Evergreen Terrace Apt 3B, San Antonio, TX 78207"}], confidence_score=0.9200, source_priority=85, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="accommodation_requested_self", field_value="no", confidence_score=0.9300, source_priority=85, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="accommodation_requested_spouse", field_value="no", confidence_score=0.9300, source_priority=85, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="accommodation_requested_children", field_value="no", confidence_score=0.9300, source_priority=85, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="petitioner_can_read_english", field_value="yes", confidence_score=0.9000, source_priority=80, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="beneficiary_can_read_english", field_value="yes", confidence_score=0.9000, source_priority=80, status="confirmed"),
                CaseCanonicalField(case_id=case.id, source_document_id=source_document_id, field_key="additional_information", field_value="Joint filing with one child, shared residence, shared finances, and six months of joint bank statements already uploaded.", confidence_score=0.8600, source_priority=75, status="confirmed"),
            ])
    session.add_all(fields)
    await session.flush()


async def seed_inconsistencies(session: Any, cases: dict[str, Case]) -> None:
    inconsistencies = [
        Inconsistency(case_id=cases["case_1"].id, field_key="beneficiary.date_of_birth", severity="critical", status="open", description="Questionnaire is missing date of birth while passport extraction contains one.", evidence_payload={"sources": ["questionnaire", "passport"]}, resolution_notes=None, resolved_by_user_id=None, resolved_at=None),
        Inconsistency(case_id=cases["case_2"].id, field_key="beneficiary.date_of_birth", severity="high", status="open", description="Passport and birth certificate disagree on the beneficiary date of birth.", evidence_payload={"sources": ["passport", "birth_certificate"]}, resolution_notes=None, resolved_by_user_id=None, resolved_at=None),
        Inconsistency(case_id=cases["case_3"].id, field_key="petition.category", severity="medium", status="resolved", description="Questionnaire category was corrected to match attorney review.", evidence_payload={"sources": ["questionnaire", "canonical_fields"]}, resolution_notes="Category normalized to IR1.", resolved_by_user_id="staff-attorney-001", resolved_at=seeded_at(5)),
        Inconsistency(case_id=cases["case_4"].id, field_key="job.offer_active", severity="low", status="dismissed", description="Employer letter date mismatch determined not material.", evidence_payload={"sources": ["questionnaire", "evidence"]}, resolution_notes="Dismissed during final QA review.", resolved_by_user_id="staff-qa-001", resolved_at=seeded_at(3)),
    ]
    session.add_all(inconsistencies)
    await session.flush()


async def seed_reviews(session: Any, cases: dict[str, Case]) -> None:
    reviews = [
        Review(case_id=cases["case_1"].id, review_type="paralegal", reviewer_reference="staff-paralegal-001", decision="fix_required", notes="Missing DOB and marriage certificate need follow-up.", reviewed_at=seeded_at(15)),
        Review(case_id=cases["case_2"].id, review_type="paralegal", reviewer_reference="staff-paralegal-001", decision="approved", notes="Packet is complete pending attorney review of DOB discrepancy.", reviewed_at=seeded_at(10)),
        Review(case_id=cases["case_3"].id, review_type="attorney", reviewer_reference="staff-attorney-001", decision="approved", notes="Case is approved for submission.", reviewed_at=seeded_at(4)),
        Review(case_id=cases["case_3"].id, review_type="qa", reviewer_reference="staff-qa-001", decision="approved", notes="QA verified packet and generated form.", reviewed_at=seeded_at(3)),
        Review(case_id=cases["case_4"].id, review_type="attorney", reviewer_reference="staff-attorney-001", decision="approved", notes="Employment petition approved before filing.", reviewed_at=seeded_at(8)),
        Review(case_id=cases["case_5"].id, review_type="attorney", reviewer_reference="staff-attorney-001", decision="approved", notes="Closed case was approved before submission.", reviewed_at=seeded_at(110)),
        Review(case_id=cases["case_5"].id, review_type="qa", reviewer_reference="staff-qa-001", decision="approved", notes="Final QA complete before archival.", reviewed_at=seeded_at(100)),
        Review(case_id=cases["case_6"].id, review_type="attorney", reviewer_reference="staff-attorney-001", decision="approved", notes="Humanitarian filing approved for submission before gateway failure.", reviewed_at=seeded_at(7)),
        Review(case_id=cases["case_7"].id, review_type="attorney", reviewer_reference="staff-attorney-001", decision="changes_requested", notes="Demo ROC listo para revision; confirmar evidencia conjunta faltante antes del firmado final de la I-751.", reviewed_at=seeded_at(2)),
    ]
    session.add_all(reviews)
    await session.flush()


async def seed_packets(session: Any, cases: dict[str, Case], documents: dict[str, dict[str, Document]]) -> None:
    packets = []
    required_document_types = {
        "passport",
        "birth_certificate",
        "marriage_certificate",
        "evidence",
        "conditional_resident_card",
        "roc_questionnaire",
        "joint_tax_returns",
        "joint_bank_statements",
        "relationship_photos",
    }
    for index, case_key in enumerate(["case_2", "case_3", "case_4", "case_5", "case_6", "case_7"], start=1):
        case = cases[case_key]
        current_documents = [document for document in documents[case_key].values() if document.is_current]
        packets.append(
            CasePacket(
                case_id=case.id,
                packet_version=1,
                packet_status="generated",
                generated_by_reference="staff-paralegal-001",
                summary_payload={"case_id": str(case.id), "case_number": case.case_number, "case_type": case.case_type, "case_status": case.status, "title": case.title},
                document_index=[{"document_id": str(document.id), "document_type": document.document_type, "title": document.original_filename, "original_filename": document.original_filename, "priority": position, "section": "Supporting Documents", "document_status": document.document_status, "processing_status": document.processing_status} for position, document in enumerate(current_documents, start=1)],
                checklist_payload=[{"item_key": f"document:{document.document_type}", "label": document.document_type.replace("_", " ").title(), "status": "ready", "required": document.document_type in required_document_types} for document in current_documents],
                export_artifact=build_packet_export(case.case_number, 1),
                generation_notes=f"Seed packet {index} for QA flows.",
                generated_at=seeded_at(8 - index),
            )
        )
    session.add_all(packets)
    await session.flush()


async def seed_generated_forms(session: Any, cases: dict[str, Case], forms: dict[str, Form]) -> None:
    generated_forms = [
        GeneratedForm(case_id=cases["case_1"].id, form_id=forms["family-based"].id, draft_version=1, status="review_pending", generated_payload=build_form_payload(form_code="I-130", form_name=forms["family-based"].form_name, form_version=1, fields={"beneficiary.full_name": "LUIS MARTINEZ", "beneficiary.date_of_birth": None, "petition.category": "ir1"}), warnings_payload=[{"type": "missing_required_field", "form_field_key": "beneficiary.date_of_birth", "canonical_field_key": "beneficiary.date_of_birth", "message": "Required canonical field is missing."}], export_path="/app/storage/generated-forms/CASE-QA-0001/I-130/draft-v1.json", review_notes=None, generated_at=seeded_at(14), reviewed_by_user_id=None, reviewed_at=None),
        GeneratedForm(case_id=cases["case_2"].id, form_id=forms["family-based"].id, draft_version=1, status="approved", generated_payload=build_form_payload(form_code="I-130", form_name=forms["family-based"].form_name, form_version=1, fields={"beneficiary.full_name": "DIEGO RAMIREZ", "beneficiary.date_of_birth": "1988-08-22", "petition.category": "ir5"}), warnings_payload=[], export_path="/app/storage/generated-forms/CASE-QA-0002/I-130/draft-v1.json", review_notes="Approved for attorney review.", generated_at=seeded_at(9), reviewed_by_user_id="staff-paralegal-001", reviewed_at=seeded_at(8)),
        GeneratedForm(case_id=cases["case_3"].id, form_id=forms["family-based"].id, draft_version=1, status="approved", generated_payload=build_form_payload(form_code="I-130", form_name=forms["family-based"].form_name, form_version=1, fields={"beneficiary.full_name": "LUCIA FERNANDEZ", "beneficiary.date_of_birth": "1990-02-09", "petition.category": "ir1"}), warnings_payload=[], export_path="/app/storage/generated-forms/CASE-QA-0003/I-130/draft-v1.json", review_notes="Attorney approved.", generated_at=seeded_at(5), reviewed_by_user_id="staff-attorney-001", reviewed_at=seeded_at(4)),
        GeneratedForm(case_id=cases["case_4"].id, form_id=forms["employment-based"].id, draft_version=1, status="approved", generated_payload=build_form_payload(form_code="I-140", form_name=forms["employment-based"].form_name, form_version=1, fields={"beneficiary.full_name": "Carlos Lopez", "job.offer_active": "yes", "petition.type": "eb2_niw"}), warnings_payload=[], export_path="/app/storage/generated-forms/CASE-QA-0004/I-140/draft-v1.json", review_notes="Filed from approved draft.", generated_at=seeded_at(12), reviewed_by_user_id="staff-attorney-001", reviewed_at=seeded_at(9)),
        GeneratedForm(case_id=cases["case_5"].id, form_id=forms["family-based"].id, draft_version=2, status="approved", generated_payload=build_form_payload(form_code="I-130", form_name=forms["family-based"].form_name, form_version=1, fields={"beneficiary.full_name": "MARIANA TORRES", "beneficiary.date_of_birth": "1994-07-30", "petition.category": "ir1"}), warnings_payload=[], export_path="/app/storage/generated-forms/CASE-QA-0005/I-130/draft-v2.json", review_notes="Historical approved draft retained for closed case.", generated_at=seeded_at(115), reviewed_by_user_id="staff-attorney-001", reviewed_at=seeded_at(112)),
        GeneratedForm(case_id=cases["case_6"].id, form_id=forms["humanitarian"].id, draft_version=1, status="approved", generated_payload=build_form_payload(form_code="I-589", form_name=forms["humanitarian"].form_name, form_version=1, fields={"applicant.full_name": "Jorge Castillo", "program.selected": "asylum", "narrative.summary": "Fear-based claim supported by declarations and country conditions."}), warnings_payload=[], export_path="/app/storage/generated-forms/CASE-QA-0006/I-589/draft-v1.json", review_notes="Approved before transmission failure.", generated_at=seeded_at(7), reviewed_by_user_id="staff-attorney-001", reviewed_at=seeded_at(6)),
        GeneratedForm(case_id=cases["case_7"].id, form_id=forms["roc-i751"].id, draft_version=1, status="review_pending", generated_payload=build_form_payload(form_code="I-751", form_name=forms["roc-i751"].form_name, form_version=1, fields={"part_1.last_name": "SABOGAL FUENTES", "part_1.first_name": "LUZ ANGELA MARIA", "part_1.a_number": "A123456789", "part_1.date_of_birth": "1986-04-02", "part_1.marriage_date": "2021-06-18", "part_1.spouse_last_name": "FUENTES", "part_1.spouse_first_name": "DANIEL ALEJANDRO", "part_1.children_count": 1, "part_1.mailing_address": "742 Evergreen Terrace Apt 3B, San Antonio, TX 78207", "part_7.signature_required": True}), warnings_payload=[{"type": "attorney_review_required", "form_field_key": "part_3.criminal_history", "canonical_field_key": "arrest_history", "message": "Confirmar nuevamente que no existan arrestos, detenciones o citaciones no reportadas."}], export_path="/app/storage/generated-forms/CASE-QA-0007/I-751/draft-v1.json", review_notes="Borrador demo de I-751 armado a partir del cuestionario y evidencia ROC.", generated_at=seeded_at(1), reviewed_by_user_id=None, reviewed_at=None),
    ]
    session.add_all(generated_forms)
    await session.flush()


async def seed_submissions(session: Any, cases: dict[str, Case]) -> None:
    submissions = [
        CaseSubmission(case_id=cases["case_3"].id, status="approved_for_submission", approved_for_submission_at=seeded_at(2), approved_by_user_id="staff-attorney-001", submitted_at=None, submitted_by_user_id=None, submission_reference=None, failed_at=None, failed_by_user_id=None, failure_reason=None),
        CaseSubmission(case_id=cases["case_4"].id, status="submitted", approved_for_submission_at=seeded_at(7), approved_by_user_id="staff-attorney-001", submitted_at=seeded_at(2), submitted_by_user_id="staff-paralegal-001", submission_reference="USCIS-EB2NIW-0004", failed_at=None, failed_by_user_id=None, failure_reason=None),
        CaseSubmission(case_id=cases["case_5"].id, status="submitted", approved_for_submission_at=seeded_at(111), approved_by_user_id="staff-attorney-001", submitted_at=seeded_at(108), submitted_by_user_id="staff-paralegal-001", submission_reference="USCIS-IR1-0005", failed_at=None, failed_by_user_id=None, failure_reason=None),
        CaseSubmission(case_id=cases["case_6"].id, status="failed", approved_for_submission_at=seeded_at(6), approved_by_user_id="staff-attorney-001", submitted_at=None, submitted_by_user_id=None, submission_reference=None, failed_at=seeded_at(1), failed_by_user_id="staff-paralegal-001", failure_reason="Government gateway timeout during submission."),
    ]
    session.add_all(submissions)
    await session.flush()


async def seed_audit_logs(session: Any, cases: dict[str, Case]) -> None:
    logs = [
        AuditLog(case_id=cases["case_1"].id, entity_type="document", entity_id="seed-case-1-passport", action="document_uploaded", actor_reference="staff-paralegal-001", payload={"case_number": cases["case_1"].case_number, "document_type": "passport"}, occurred_at=seeded_at(18)),
        AuditLog(case_id=cases["case_1"].id, entity_type="case_readiness", entity_id=str(cases["case_1"].id), action="case_readiness_validated", actor_reference="staff-paralegal-001", payload={"target": "attorney_review", "result": "blocked"}, occurred_at=seeded_at(14)),
        AuditLog(case_id=cases["case_2"].id, entity_type="document", entity_id="seed-case-2-passport-v2", action="document_replaced", actor_reference="staff-paralegal-001", payload={"case_number": cases["case_2"].case_number, "version": 2}, occurred_at=seeded_at(14)),
        AuditLog(case_id=cases["case_2"].id, entity_type="inconsistency", entity_id="seed-case-2-dob", action="inconsistency_detected", actor_reference="system-seed", payload={"severity": "high"}, occurred_at=seeded_at(10)),
        AuditLog(case_id=cases["case_3"].id, entity_type="generated_form", entity_id="seed-case-3-form", action="generated_form_approved", actor_reference="staff-attorney-001", payload={"form_code": "I-130"}, occurred_at=seeded_at(4)),
        AuditLog(case_id=cases["case_3"].id, entity_type="case_submission", entity_id="seed-case-3-submission", action="case_submission_approved", actor_reference="staff-attorney-001", payload={"notes": "Ready for submission"}, occurred_at=seeded_at(2)),
        AuditLog(case_id=cases["case_4"].id, entity_type="case_submission", entity_id="seed-case-4-submission", action="case_submitted", actor_reference="staff-paralegal-001", payload={"submission_reference": "USCIS-EB2NIW-0004"}, occurred_at=seeded_at(2)),
        AuditLog(case_id=cases["case_5"].id, entity_type="case", entity_id=str(cases["case_5"].id), action="case_closed", actor_reference="staff-admin-001", payload={"notes": "Closed after successful filing."}, occurred_at=seeded_at(90)),
        AuditLog(case_id=cases["case_6"].id, entity_type="case_submission", entity_id="seed-case-6-submission", action="case_submission_failed", actor_reference="staff-paralegal-001", payload={"failure_reason": "Government gateway timeout during submission."}, occurred_at=seeded_at(1)),
        AuditLog(case_id=cases["case_7"].id, entity_type="client_portal_access", entity_id="seed-case-7-portal", action="client_portal_access_seeded", actor_reference="system-seed", payload={"token_last4": SEED_PORTAL_CREDENTIALS["case_7"]["token"][-4:], "passcode_hint": "See seed reference file."}, occurred_at=seeded_at(1)),
        AuditLog(case_id=cases["case_7"].id, entity_type="generated_form", entity_id="seed-case-7-i751", action="generated_form_created", actor_reference="system-seed", payload={"form_code": "I-751", "status": "review_pending"}, occurred_at=seeded_at(1)),
    ]
    session.add_all(logs)
    await session.flush()


async def seed_case_checklists(session: Any, cases: dict[str, Case]) -> None:
    await ensure_roc_i751_defaults(session, "roc-i751")
    template = await session.scalar(select(DocumentChecklistTemplate).where(DocumentChecklistTemplate.case_type == "roc-i751"))
    template_items: list[DocumentChecklistTemplateItem] = []
    if template is not None:
        result = await session.scalars(
            select(DocumentChecklistTemplateItem)
            .where(DocumentChecklistTemplateItem.template_id == template.id)
            .order_by(DocumentChecklistTemplateItem.display_order)
        )
        template_items = list(result)

    checklist_items = [
        CaseDocumentChecklistItem(
            case_id=cases["case_1"].id,
            label="Passport biographic page",
            document_type="passport",
            display_order=1,
            applies=True,
            requested=True,
            received=False,
            validated=False,
            observations="Still missing from intake packet.",
            copy_only=True,
            is_manual=True,
        ),
        CaseDocumentChecklistItem(
            case_id=cases["case_1"].id,
            label="Birth certificate",
            document_type="birth_certificate",
            display_order=2,
            applies=True,
            requested=True,
            received=False,
            validated=False,
            observations="Client must upload certified copy.",
            copy_only=True,
            is_manual=True,
        ),
    ]

    received_document_types = {
        "conditional_resident_card",
        "marriage_certificate",
        "joint_tax_returns",
        "joint_bank_statements",
        "children_birth_certificates",
        "relationship_photos",
        "roc_questionnaire",
    }

    for index, template_item in enumerate(template_items, start=1):
        received = template_item.document_type in received_document_types
        checklist_items.append(
            CaseDocumentChecklistItem(
                case_id=cases["case_7"].id,
                template_item_id=template_item.id,
                label=template_item.label,
                document_type=template_item.document_type,
                display_order=index,
                applies=template_item.default_applies or received,
                requested=template_item.default_applies,
                received=received,
                validated=received and template_item.document_type in {"conditional_resident_card", "marriage_certificate", "joint_tax_returns"},
                observations=(
                    "Marcado durante la entrevista ROC."
                    if template_item.default_applies
                    else "No aplica por ahora; puede activarse si surge durante la revision."
                ),
                color_required=template_item.color_required,
                english_translation_required=template_item.english_translation_required,
                signed_copy_required=template_item.signed_copy_required,
                original_required=template_item.original_required,
                copy_only=template_item.copy_only,
                is_manual=False,
            )
        )

    session.add_all(checklist_items)
    await session.flush()


async def seed_client_portal_accesses(session: Any, cases: dict[str, Case]) -> None:
    accesses = []
    for case_key, credentials in SEED_PORTAL_CREDENTIALS.items():
        token = credentials["token"]
        passcode = credentials["passcode"]
        accesses.append(
            ClientPortalAccess(
                case_id=cases[case_key].id,
                token_hash=sha_for(token),
                token_last4=token[-4:],
                passcode_hash=sha_for(passcode),
                access_session_hash=None,
                access_session_expires_at=None,
                instructions=credentials["instructions"],
                expires_at=BASE_TIME + timedelta(days=21),
                is_active=True,
                last_accessed_at=None,
                failed_access_attempt_count=0,
                last_failed_access_at=None,
                locked_until=None,
            )
        )
    session.add_all(accesses)
    await session.flush()


def write_reference_files(output_root: Path, cases: dict[str, Case]) -> None:
    reference_root = output_root / "seed-reference"
    reference_root.mkdir(parents=True, exist_ok=True)
    (reference_root / "staff-users.json").write_text(json.dumps({"users": INTERNAL_USERS}, indent=2), encoding="utf-8")
    (reference_root / "case-types.json").write_text(json.dumps({"case_types": CASE_TYPE_CATALOG}, indent=2), encoding="utf-8")
    (reference_root / "cases.json").write_text(
        json.dumps(
            {
                "cases": [
                    {"case_number": case.case_number, "case_type": case.case_type, "status": case.status, "title": case.title, "summary": case.summary}
                    for case in cases.values()
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (reference_root / "client-portal-demo.json").write_text(
        json.dumps(
            {
                "portals": [
                    {
                        "case_number": cases[case_key].case_number,
                        "case_title": cases[case_key].title,
                        "portal_path": f"/portal/{credentials['token']}",
                        "token": credentials["token"],
                        "passcode": credentials["passcode"],
                    }
                    for case_key, credentials in SEED_PORTAL_CREDENTIALS.items()
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    asyncio.run(seed())
