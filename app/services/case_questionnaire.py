from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.questionnaire_answer import QuestionnaireAnswer
from app.models.questionnaire_question import QuestionnaireQuestion
from app.models.questionnaire import Questionnaire
from app.models.questionnaire_template import QuestionnaireTemplate
from app.repositories.questionnaire import QuestionnaireRepository
from app.repositories.audit_log import AuditLogRepository
from app.repositories.questionnaire_answer import QuestionnaireAnswerRepository
from app.repositories.questionnaire_template import QuestionnaireTemplateRepository
from app.schemas.case_questionnaire import (
    CaseQuestionnaireAnswerUpdateRequest,
    CaseQuestionnaireAnswersUpsertRequest,
    CaseQuestionnaireRead,
    QuestionnaireAnswerPayload,
    QuestionnaireAnswerRead,
    QuestionnaireQuestionRead,
    QuestionnaireSectionRead,
    QuestionnaireTemplateSummaryRead,
)


class CaseQuestionnaireService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.template_repository = QuestionnaireTemplateRepository(session)
        self.questionnaire_repository = QuestionnaireRepository(session)
        self.answer_repository = QuestionnaireAnswerRepository(session)
        self.audit_log_repository = AuditLogRepository(session)

    async def get_case_questionnaire(self, case_id: uuid.UUID) -> CaseQuestionnaireRead:
        case = await self._get_case(case_id)
        questionnaire_instance = await self.questionnaire_repository.get_latest_for_case(case.id)
        template = await self._get_template_for_case(case, questionnaire_instance)
        answers = await self.answer_repository.list_for_case(case.id)
        answer_map = {answer.question_id: answer for answer in answers}

        sections = [
            QuestionnaireSectionRead(
                id=section.id,
                title=section.title,
                description=section.description,
                display_order=section.display_order,
                questions=[
                    QuestionnaireQuestionRead(
                        id=question.id,
                        key=question.key,
                        prompt=question.prompt,
                        help_text=question.help_text,
                        input_type=question.input_type,
                        is_required=question.is_required,
                        display_order=question.display_order,
                        options=question.options,
                        validation_rules=question.validation_rules,
                        conditional_rules=question.conditional_rules,
                        field_config=question.field_config,
                        answer=(
                            QuestionnaireAnswerRead.model_validate(answer_map[question.id])
                            if question.id in answer_map
                            else None
                        ),
                    )
                    for question in section.questions
                ],
            )
            for section in template.sections
        ]

        return CaseQuestionnaireRead(
            case_id=case.id,
            case_type=case.case_type,
            questionnaire=QuestionnaireTemplateSummaryRead.model_validate(template),
            questionnaire_instance_id=questionnaire_instance.id if questionnaire_instance is not None else None,
            questionnaire_instance_status=questionnaire_instance.status if questionnaire_instance is not None else None,
            questionnaire_instance_version=questionnaire_instance.template_version if questionnaire_instance is not None else None,
            sections=sections,
        )

    async def upsert_answers(
        self,
        case_id: uuid.UUID,
        payload: CaseQuestionnaireAnswersUpsertRequest,
    ) -> list[QuestionnaireAnswer]:
        case = await self._get_case(case_id)
        template = await self._get_template_for_case(case)
        questions = self._template_question_map(template)

        persisted_answers: list[QuestionnaireAnswer] = []
        for answer_input in payload.answers:
            question = self._get_question_or_raise(answer_input.question_id, questions)
            normalized_values = self._normalize_answer_payload(question, answer_input.value)

            existing_answer = await self.answer_repository.get_for_case_and_question(case.id, question.id)
            if existing_answer is None:
                answer = await self.answer_repository.create(
                    {
                        "case_id": case.id,
                        "question_id": question.id,
                        **normalized_values,
                    }
                )
                await self._create_audit_log(
                    case_id=case.id,
                    entity_id=answer.id,
                    action="questionnaire_answer_created",
                    actor_reference=payload.actor_reference,
                    payload={
                        "case_id": str(case.id),
                        "question_id": str(question.id),
                        "question_key": question.key,
                    },
                )
                persisted_answers.append(answer)
                continue

            answer = await self.answer_repository.update(existing_answer, normalized_values)
            await self._create_audit_log(
                case_id=case.id,
                entity_id=answer.id,
                action="questionnaire_answer_updated",
                actor_reference=payload.actor_reference,
                payload={
                    "case_id": str(case.id),
                    "question_id": str(question.id),
                    "question_key": question.key,
                },
            )
            persisted_answers.append(answer)

        await self.session.commit()
        return persisted_answers

    async def update_answer(
        self,
        case_id: uuid.UUID,
        answer_id: uuid.UUID,
        payload: CaseQuestionnaireAnswerUpdateRequest,
    ) -> QuestionnaireAnswer:
        case = await self._get_case(case_id)
        template = await self._get_template_for_case(case)
        questions = self._template_question_map(template)

        answer = await self.answer_repository.get_for_case_by_id(case.id, answer_id)
        if answer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="questionnaire answer not found",
            )

        question = self._get_question_or_raise(answer.question_id, questions)
        normalized_values = self._normalize_answer_payload(question, payload.value)
        updated_answer = await self.answer_repository.update(answer, normalized_values)
        await self._create_audit_log(
            case_id=case.id,
            entity_id=updated_answer.id,
            action="questionnaire_answer_updated",
            actor_reference=payload.actor_reference,
            payload={
                "case_id": str(case.id),
                "question_id": str(question.id),
                "question_key": question.key,
            },
        )
        await self.session.commit()
        return updated_answer

    async def _get_case(self, case_id: uuid.UUID) -> Case:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
        return case

    async def _get_template_for_case(
        self,
        case: Case,
        questionnaire_instance: Questionnaire | None = None,
    ) -> QuestionnaireTemplate:
        template = None
        if questionnaire_instance is not None and questionnaire_instance.template_id is not None:
            template = await self.template_repository.get_full(questionnaire_instance.template_id)
        if template is None:
            template = await self.template_repository.get_active_for_case_type(case.case_type)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"questionnaire template not found for case type '{case.case_type}'",
            )
        return template

    def _template_question_map(
        self,
        template: QuestionnaireTemplate,
    ) -> dict[uuid.UUID, QuestionnaireQuestion]:
        return {
            question.id: question
            for section in template.sections
            for question in section.questions
        }

    def _get_question_or_raise(
        self,
        question_id: uuid.UUID,
        available_questions: dict[uuid.UUID, QuestionnaireQuestion],
    ) -> QuestionnaireQuestion:
        question = available_questions.get(question_id)
        if question is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="question does not belong to the questionnaire for this case",
            )
        return question

    def _normalize_answer_payload(
        self,
        question: QuestionnaireQuestion,
        payload: QuestionnaireAnswerPayload,
    ) -> dict[str, Any]:
        values = {
            "answer_text": None,
            "answer_date": None,
            "answer_boolean": None,
            "answer_choice": None,
            "answer_choices": None,
            "answer_json": None,
        }

        if question.input_type in {"text", "textarea"}:
            if payload.answer_text is None:
                self._raise_invalid_answer(question.input_type)
            values["answer_text"] = payload.answer_text
            return values

        if question.input_type == "date":
            if payload.answer_date is None:
                self._raise_invalid_answer(question.input_type)
            values["answer_date"] = payload.answer_date
            return values

        if question.input_type in {"boolean", "checkbox"}:
            if payload.answer_boolean is None:
                self._raise_invalid_answer(question.input_type)
            values["answer_boolean"] = payload.answer_boolean
            return values

        allowed_options = {
            option["value"] for option in (question.options or []) if isinstance(option, dict) and "value" in option
        }

        if question.input_type in {"single_select", "radio", "select"}:
            if payload.answer_choice is None:
                self._raise_invalid_answer(question.input_type)
            if allowed_options and payload.answer_choice not in allowed_options:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="answer choice is not valid for this question",
                )
            values["answer_choice"] = payload.answer_choice
            return values

        if question.input_type == "multi_select":
            if payload.answer_choices is None:
                self._raise_invalid_answer(question.input_type)
            invalid_options = [choice for choice in payload.answer_choices if allowed_options and choice not in allowed_options]
            if invalid_options:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="one or more answer choices are not valid for this question",
                )
            values["answer_choices"] = payload.answer_choices
            return values

        if question.input_type in {"json", "repeatable_group"}:
            if payload.answer_json is None:
                self._raise_invalid_answer(question.input_type)
            values["answer_json"] = payload.answer_json
            return values

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported question input type '{question.input_type}'",
        )

    def _raise_invalid_answer(self, expected_type: str) -> None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"answer payload does not match expected type '{expected_type}'",
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
                "entity_type": "questionnaire_answer",
                "entity_id": str(entity_id),
                "action": action,
                "actor_reference": actor_reference,
                "payload": payload,
                "occurred_at": datetime.now(UTC),
            }
        )
