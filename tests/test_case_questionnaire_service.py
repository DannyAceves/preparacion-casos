from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.case import Case
from app.services.case_questionnaire import CaseQuestionnaireService
from app.schemas.case_questionnaire import (
    CaseQuestionnaireAnswerUpdateRequest,
    CaseQuestionnaireAnswersUpsertRequest,
    QuestionnaireAnswerPayload,
)


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class FakeSession:
    cases: dict[uuid.UUID, object]
    committed: bool = False

    async def get(self, model: type[object], entity_id: uuid.UUID) -> object | None:
        if model is Case:
            return self.cases.get(entity_id)
        return None

    async def commit(self) -> None:
        self.committed = True


@dataclass
class FakeTemplateRepository:
    template_by_case_type: dict[str, object]

    async def get_active_for_case_type(self, case_type: str) -> object | None:
        return self.template_by_case_type.get(case_type)


@dataclass
class FakeAnswerRepository:
    answers: list[object] = field(default_factory=list)

    async def list_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [answer for answer in self.answers if answer.case_id == case_id]

    async def get_for_case_and_question(self, case_id: uuid.UUID, question_id: uuid.UUID) -> object | None:
        for answer in self.answers:
            if answer.case_id == case_id and answer.question_id == question_id:
                return answer
        return None

    async def get_for_case_by_id(self, case_id: uuid.UUID, answer_id: uuid.UUID) -> object | None:
        for answer in self.answers:
            if answer.case_id == case_id and answer.id == answer_id:
                return answer
        return None

    async def create(self, data: dict) -> object:
        answer = SimpleNamespace(
            id=uuid.uuid4(),
            created_at=_now(),
            updated_at=_now(),
            **data,
        )
        self.answers.append(answer)
        return answer

    async def update(self, entity: object, data: dict) -> object:
        for field_name, field_value in data.items():
            setattr(entity, field_name, field_value)
        entity.updated_at = _now()
        return entity


@dataclass
class FakeAuditLogRepository:
    entries: list[dict] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        self.entries.append(data)
        return SimpleNamespace(**data)


def build_questionnaire_fixture() -> tuple[uuid.UUID, object, object, object, object]:
    case_id = uuid.uuid4()
    question_text_id = uuid.uuid4()
    question_date_id = uuid.uuid4()
    case = SimpleNamespace(id=case_id, case_type="family-based")
    text_question = SimpleNamespace(
        id=question_text_id,
        key="beneficiary_full_name",
        prompt="What is the beneficiary full legal name?",
        help_text=None,
        input_type="text",
        is_required=True,
        display_order=1,
        options=None,
        validation_rules=None,
    )
    date_question = SimpleNamespace(
        id=question_date_id,
        key="beneficiary_date_of_birth",
        prompt="What is the beneficiary date of birth?",
        help_text=None,
        input_type="date",
        is_required=True,
        display_order=2,
        options=None,
        validation_rules=None,
    )
    section = SimpleNamespace(
        id=uuid.uuid4(),
        title="Beneficiary Information",
        description=None,
        display_order=1,
        questions=[text_question, date_question],
    )
    template = SimpleNamespace(
        id=uuid.uuid4(),
        case_type="family-based",
        title="Family-Based Intake Questionnaire",
        description=None,
        status="active",
        version=1,
        sections=[section],
    )
    return case_id, case, template, text_question, date_question


@pytest.mark.asyncio
async def test_get_case_questionnaire_returns_template_and_answers() -> None:
    case_id, case, template, text_question, _ = build_questionnaire_fixture()
    existing_answer = SimpleNamespace(
        id=uuid.uuid4(),
        case_id=case_id,
        question_id=text_question.id,
        answer_text="Demo Applicant",
        answer_date=None,
        answer_boolean=None,
        answer_choice=None,
        answer_choices=None,
        answer_json=None,
        created_at=_now(),
        updated_at=_now(),
    )

    session = FakeSession(cases={case_id: case})
    service = CaseQuestionnaireService(session)
    service.template_repository = FakeTemplateRepository({"family-based": template})
    service.answer_repository = FakeAnswerRepository([existing_answer])
    service.audit_log_repository = FakeAuditLogRepository()

    questionnaire = await service.get_case_questionnaire(case_id)

    assert questionnaire.case_id == case_id
    assert questionnaire.questionnaire.id == template.id
    assert questionnaire.sections[0].questions[0].answer is not None
    assert questionnaire.sections[0].questions[0].answer.answer_text == "Demo Applicant"
    assert questionnaire.sections[0].questions[1].answer is None


@pytest.mark.asyncio
async def test_upsert_answers_updates_existing_without_duplicates_and_audits() -> None:
    case_id, case, template, text_question, _ = build_questionnaire_fixture()
    existing_answer = SimpleNamespace(
        id=uuid.uuid4(),
        case_id=case_id,
        question_id=text_question.id,
        answer_text="Old Value",
        answer_date=None,
        answer_boolean=None,
        answer_choice=None,
        answer_choices=None,
        answer_json=None,
        created_at=_now(),
        updated_at=_now(),
    )

    session = FakeSession(cases={case_id: case})
    answer_repository = FakeAnswerRepository([existing_answer])
    audit_repository = FakeAuditLogRepository()

    service = CaseQuestionnaireService(session)
    service.template_repository = FakeTemplateRepository({"family-based": template})
    service.answer_repository = answer_repository
    service.audit_log_repository = audit_repository

    payload = CaseQuestionnaireAnswersUpsertRequest(
        actor_reference="lawyer-1",
        answers=[
            {
                "question_id": text_question.id,
                "value": {"answer_text": "Updated Value"},
            }
        ],
    )

    answers = await service.upsert_answers(case_id, payload)

    assert len(answers) == 1
    assert len(answer_repository.answers) == 1
    assert answer_repository.answers[0].answer_text == "Updated Value"
    assert audit_repository.entries[0]["action"] == "questionnaire_answer_updated"
    assert session.committed is True


@pytest.mark.asyncio
async def test_upsert_answers_rejects_question_outside_case_questionnaire() -> None:
    case_id, case, template, _, _ = build_questionnaire_fixture()
    session = FakeSession(cases={case_id: case})

    service = CaseQuestionnaireService(session)
    service.template_repository = FakeTemplateRepository({"family-based": template})
    service.answer_repository = FakeAnswerRepository()
    service.audit_log_repository = FakeAuditLogRepository()

    payload = CaseQuestionnaireAnswersUpsertRequest(
        answers=[
            {
                "question_id": uuid.uuid4(),
                "value": {"answer_text": "Invalid"},
            }
        ]
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.upsert_answers(case_id, payload)

    assert exc_info.value.status_code == 400
    assert "does not belong" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_answer_validates_expected_type() -> None:
    case_id, case, template, _, date_question = build_questionnaire_fixture()
    existing_answer = SimpleNamespace(
        id=uuid.uuid4(),
        case_id=case_id,
        question_id=date_question.id,
        answer_text=None,
        answer_date=date(1990, 1, 1),
        answer_boolean=None,
        answer_choice=None,
        answer_choices=None,
        answer_json=None,
        created_at=_now(),
        updated_at=_now(),
    )

    session = FakeSession(cases={case_id: case})
    service = CaseQuestionnaireService(session)
    service.template_repository = FakeTemplateRepository({"family-based": template})
    service.answer_repository = FakeAnswerRepository([existing_answer])
    service.audit_log_repository = FakeAuditLogRepository()

    payload = CaseQuestionnaireAnswerUpdateRequest(
        actor_reference="lawyer-1",
        value=QuestionnaireAnswerPayload(answer_text="not a date"),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.update_answer(case_id, existing_answer.id, payload)

    assert exc_info.value.status_code == 400
    assert "expected type 'date'" in exc_info.value.detail
