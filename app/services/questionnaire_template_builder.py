from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.questionnaire import Questionnaire
from app.models.questionnaire_question import QuestionnaireQuestion
from app.models.questionnaire_section import QuestionnaireSection
from app.models.questionnaire_template import QuestionnaireTemplate
from app.repositories.questionnaire import QuestionnaireRepository
from app.repositories.questionnaire_template import QuestionnaireTemplateRepository
from app.schemas.questionnaire_template_builder import (
    QuestionnaireInstanceCreate,
    QuestionnaireTemplateBuilderCreate,
    QuestionnaireTemplateBuilderRead,
    QuestionnaireTemplateBuilderUpdate,
    QuestionnaireTemplateQuestionCreate,
    QuestionnaireTemplateSectionCreate,
    QuestionnaireTemplateVersionCreate,
)


class QuestionnaireTemplateBuilderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.template_repository = QuestionnaireTemplateRepository(session)
        self.questionnaire_repository = QuestionnaireRepository(session)

    async def list_templates(self, case_type: str | None = None) -> list[QuestionnaireTemplate]:
        return await self.template_repository.list_templates(case_type)

    async def get_template(self, template_id: uuid.UUID) -> QuestionnaireTemplate:
        template = await self.template_repository.get_full(template_id)
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="questionnaire template not found")
        return template

    async def create_template(
        self,
        payload: QuestionnaireTemplateBuilderCreate,
    ) -> QuestionnaireTemplate:
        self._validate_sections(payload.sections)

        latest = await self.template_repository.get_latest_version_for_case_type(payload.case_type)
        version = (latest.version + 1) if latest is not None else 1

        template = QuestionnaireTemplate(
            case_type=payload.case_type,
            title=payload.title,
            description=payload.description,
            status=payload.status,
            version=version,
        )
        template.sections = self._build_sections(payload.sections)
        self.session.add(template)

        if payload.status == "active":
            await self._deactivate_other_templates(payload.case_type)

        await self.session.commit()
        return await self.get_template(template.id)

    async def update_template(
        self,
        template_id: uuid.UUID,
        payload: QuestionnaireTemplateBuilderUpdate,
    ) -> QuestionnaireTemplate:
        template = await self.get_template(template_id)
        if template.status == "active":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="active templates cannot be edited directly; create a new version instead",
            )

        if payload.title is not None:
            template.title = payload.title
        if payload.description is not None:
            template.description = payload.description
        if payload.status is not None:
            template.status = payload.status

        if payload.sections is not None:
            self._validate_sections(payload.sections)
            template.sections.clear()
            template.sections.extend(self._build_sections(payload.sections))

        if template.status == "active":
            await self._deactivate_other_templates(template.case_type, exclude_template_id=template.id)

        await self.session.commit()
        return await self.get_template(template.id)

    async def activate_template(self, template_id: uuid.UUID) -> QuestionnaireTemplate:
        template = await self.get_template(template_id)
        await self._deactivate_other_templates(template.case_type, exclude_template_id=template.id)
        template.status = "active"
        await self.session.commit()
        return await self.get_template(template.id)

    async def create_new_version(
        self,
        template_id: uuid.UUID,
        payload: QuestionnaireTemplateVersionCreate,
    ) -> QuestionnaireTemplate:
        source = await self.get_template(template_id)
        latest = await self.template_repository.get_latest_version_for_case_type(source.case_type)
        version = (latest.version + 1) if latest is not None else (source.version + 1)

        cloned = QuestionnaireTemplate(
            case_type=source.case_type,
            title=payload.title or source.title,
            description=payload.description if payload.description is not None else source.description,
            status=payload.status,
            version=version,
        )
        cloned.sections = self._build_sections(
            [
                QuestionnaireTemplateSectionCreate(
                    title=section.title,
                    description=section.description,
                    display_order=section.display_order,
                    questions=[
                        QuestionnaireTemplateQuestionCreate(
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
                        )
                        for question in section.questions
                    ],
                )
                for section in source.sections
            ]
        )
        self.session.add(cloned)

        if payload.status == "active":
            await self._deactivate_other_templates(source.case_type)

        await self.session.commit()
        return await self.get_template(cloned.id)

    async def instantiate_for_case(
        self,
        case_id: uuid.UUID,
        payload: QuestionnaireInstanceCreate,
    ) -> Questionnaire:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")

        template = (
            await self.get_template(payload.template_id)
            if payload.template_id is not None
            else await self.template_repository.get_active_for_case_type(case.case_type)
        )
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"questionnaire template not found for case type '{case.case_type}'",
            )

        existing = await self.questionnaire_repository.get_for_case_and_template(case.id, template.id)
        if existing is not None:
            return existing

        questionnaire = Questionnaire(
            case_id=case.id,
            template_id=template.id,
            title=template.title,
            status="draft",
            version=1,
            template_version=template.version,
        )
        self.session.add(questionnaire)
        await self.session.commit()
        return questionnaire

    async def _deactivate_other_templates(
        self,
        case_type: str,
        exclude_template_id: uuid.UUID | None = None,
    ) -> None:
        stmt = (
            update(QuestionnaireTemplate)
            .where(
                QuestionnaireTemplate.case_type == case_type,
                QuestionnaireTemplate.status == "active",
            )
            .values(status="archived")
        )
        if exclude_template_id is not None:
            stmt = stmt.where(QuestionnaireTemplate.id != exclude_template_id)
        await self.session.execute(stmt)

    def _validate_sections(self, sections: list[QuestionnaireTemplateSectionCreate]) -> None:
        seen_keys: set[str] = set()
        for section in sections:
            for question in section.questions:
                normalized_key = question.key.strip()
                if normalized_key in seen_keys:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"duplicate question key '{normalized_key}' in template payload",
                    )
                seen_keys.add(normalized_key)

    def _build_sections(
        self,
        sections: list[QuestionnaireTemplateSectionCreate],
    ) -> list[QuestionnaireSection]:
        built_sections: list[QuestionnaireSection] = []
        for section_payload in sections:
            section = QuestionnaireSection(
                title=section_payload.title,
                description=section_payload.description,
                display_order=section_payload.display_order,
            )
            section.questions = [
                QuestionnaireQuestion(
                    key=question_payload.key,
                    prompt=question_payload.prompt,
                    help_text=question_payload.help_text,
                    input_type=question_payload.input_type,
                    is_required=question_payload.is_required,
                    display_order=question_payload.display_order,
                    options=(
                        [option.model_dump() for option in question_payload.options]
                        if question_payload.options
                        else None
                    ),
                    validation_rules=question_payload.validation_rules,
                    conditional_rules=question_payload.conditional_rules,
                    field_config=question_payload.field_config,
                )
                for question_payload in section_payload.questions
            ]
            built_sections.append(section)
        return built_sections
