from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.case_canonical_field import CaseCanonicalField
from app.models.client import Client
from app.models.document import Document
from app.models.form import Form
from app.models.form_field_mapping import FormFieldMapping
from app.models.generated_form import GeneratedForm
from app.models.questionnaire_answer import QuestionnaireAnswer
from app.models.questionnaire_question import QuestionnaireQuestion
from app.repositories.audit_log import AuditLogRepository
from app.repositories.case_canonical_field import CaseCanonicalFieldRepository
from app.repositories.document import DocumentRepository
from app.repositories.form import FormRepository
from app.repositories.form_field_mapping import FormFieldMappingRepository
from app.repositories.generated_form import GeneratedFormRepository
from app.schemas.generated_form import (
    AssistedFormFieldRead,
    AssistedFormFieldUpdateRequest,
    AssistedFormSectionRead,
    AssistedFormWorkspaceRead,
    GenerateFormsRequest,
    GeneratedFormRead,
    GeneratedFormDetailRead,
    GeneratedFormReviewRequest,
    GeneratedFormSuggestionRead,
    GeneratedFormTemplateRead,
)

APPROVABLE_STATUSES = {"draft", "review_pending", "fix_required"}


class GeneratedFormService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.form_repository = FormRepository(session)
        self.mapping_repository = FormFieldMappingRepository(session)
        self.generated_form_repository = GeneratedFormRepository(session)
        self.canonical_field_repository = CaseCanonicalFieldRepository(session)
        self.document_repository = DocumentRepository(session)
        self.audit_log_repository = AuditLogRepository(session)

    async def generate_for_case(
        self,
        case_id: uuid.UUID,
        payload: GenerateFormsRequest,
    ) -> list[GeneratedForm]:
        case = await self._get_case(case_id)
        forms = await self.form_repository.list_active_for_case_type(case.case_type)
        if not forms:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"forms not found for case type '{case.case_type}'",
            )

        source_bundle = await self._build_source_bundle(case.id)
        generated_forms: list[GeneratedForm] = []

        for form in forms:
            mappings = await self.mapping_repository.list_for_form(form.id)
            generated_payload, warnings_payload = self._build_form_payload(form, mappings, source_bundle)
            draft_version = await self.generated_form_repository.get_latest_draft_version(case.id, form.id) + 1
            generated_form = await self.generated_form_repository.create(
                {
                    "case_id": case.id,
                    "form_id": form.id,
                    "draft_version": draft_version,
                    "status": "review_pending" if warnings_payload else "draft",
                    "generated_payload": generated_payload,
                    "warnings_payload": warnings_payload or None,
                    "export_path": self._build_export_path(payload.export_base_path, case, form, draft_version),
                    "review_notes": None,
                    "generated_at": datetime.now(UTC),
                    "reviewed_by_user_id": None,
                    "reviewed_at": None,
                }
            )
            generated_form.form = form
            await self._create_audit_log(
                case_id=case.id,
                entity_id=generated_form.id,
                action="generated_form_created",
                actor_reference=payload.generated_by_reference,
                payload={
                    "form_code": form.form_code,
                    "draft_version": generated_form.draft_version,
                    "status": generated_form.status,
                    "warning_count": len(warnings_payload),
                },
            )
            generated_forms.append(generated_form)

        await self.session.commit()
        return generated_forms

    async def list_for_case(self, case_id: uuid.UUID) -> list[GeneratedForm]:
        await self._get_case(case_id)
        items = await self.generated_form_repository.list_for_case(case_id)
        for item in items:
            item.form = await self._get_form(item.form_id)
        return items

    async def get_detail(self, generated_form_id: uuid.UUID) -> GeneratedFormDetailRead:
        generated_form = await self._get_generated_form(generated_form_id)
        form = await self._get_form(generated_form.form_id)
        return GeneratedFormDetailRead(
            **GeneratedFormRead.model_validate(generated_form).model_dump(),
            form=GeneratedFormTemplateRead(
                form_id=form.id,
                form_code=form.form_code,
                form_name=form.form_name,
                version=form.version,
                case_type_id=form.case_type_id,
            ),
            workspace=await self.get_workspace(generated_form_id),
        )

    async def get_workspace(self, generated_form_id: uuid.UUID) -> AssistedFormWorkspaceRead:
        generated_form = await self._get_generated_form(generated_form_id)
        form = await self._get_form(generated_form.form_id)
        mappings = await self.mapping_repository.list_for_form(form.id)
        source_bundle = await self._build_source_bundle(generated_form.case_id)
        warnings_payload = self._ensure_warning_list(generated_form.warnings_payload)
        field_states = self._get_field_states(generated_form)

        sections: dict[str, AssistedFormSectionRead] = {}
        all_warnings: list[dict[str, Any]] = []

        for mapping in mappings:
            suggestions = self._build_suggestions(mapping, source_bundle)
            field_state = field_states.get(mapping.form_field_key, {})
            current_value = field_state.get("value")
            if current_value is None:
                current_value = suggestions[0].value if suggestions else None
            warnings = self._build_field_warnings(mapping, current_value, suggestions)
            all_warnings.extend(warnings)

            section_key = mapping.section_key or mapping.form_field_key.split(".")[0]
            section_title = mapping.section_title or section_key.replace("_", " ").title()
            field = AssistedFormFieldRead(
                form_field_key=mapping.form_field_key,
                canonical_field_key=mapping.canonical_field_key,
                section_key=section_key,
                section_title=section_title,
                field_label=mapping.field_label or self._humanize_key(mapping.form_field_key),
                field_type=mapping.field_type or "text",
                help_text=mapping.help_text,
                required=mapping.required,
                display_order=mapping.display_order,
                value=current_value,
                manual_override=bool(field_state.get("manual_override", False)),
                selected_source_key=field_state.get("selected_source_key"),
                selected_source_label=field_state.get("selected_source_label"),
                warnings=warnings,
                suggestions=suggestions,
            )

            if section_key not in sections:
                sections[section_key] = AssistedFormSectionRead(
                    section_key=section_key,
                    section_title=section_title,
                    display_order=self._section_display_order(section_key),
                    fields=[],
                )
            sections[section_key].fields.append(field)

        for section in sections.values():
            section.fields.sort(key=lambda item: item.display_order)

        merged_warnings = warnings_payload + [
            warning for warning in all_warnings if warning not in warnings_payload
        ]

        return AssistedFormWorkspaceRead(
            generated_form_id=generated_form.id,
            case_id=generated_form.case_id,
            status=generated_form.status,
            form=GeneratedFormTemplateRead(
                form_id=form.id,
                form_code=form.form_code,
                form_name=form.form_name,
                version=form.version,
                case_type_id=form.case_type_id,
            ),
            sections=sorted(sections.values(), key=lambda section: section.display_order),
            warnings=merged_warnings,
        )

    async def update_workspace_field(
        self,
        generated_form_id: uuid.UUID,
        form_field_key: str,
        payload: AssistedFormFieldUpdateRequest,
    ) -> GeneratedFormDetailRead:
        generated_form = await self._get_generated_form(generated_form_id)
        form = await self._get_form(generated_form.form_id)
        mappings = await self.mapping_repository.list_for_form(form.id)
        mapping_by_key = {mapping.form_field_key: mapping for mapping in mappings}
        mapping = mapping_by_key.get(form_field_key)
        if mapping is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="form field mapping not found")

        generated_payload = generated_form.generated_payload if isinstance(generated_form.generated_payload, dict) else {}
        field_states = self._get_field_states(generated_form)
        field_states[form_field_key] = {
            "value": payload.value,
            "manual_override": payload.manual_override,
            "selected_source_key": payload.selected_source_key,
            "selected_source_label": payload.selected_source_label,
            "updated_at": datetime.now(UTC).isoformat(),
        }

        fields_map = generated_payload.get("fields")
        if not isinstance(fields_map, dict):
            fields_map = {}
        fields_map[form_field_key] = payload.value
        generated_payload["fields"] = fields_map
        generated_payload["field_states"] = field_states

        source_bundle = await self._build_source_bundle(generated_form.case_id)
        warnings_payload = self._rebuild_form_warnings(mappings, field_states, source_bundle)

        updated = await self.generated_form_repository.update(
            generated_form,
            {
                "generated_payload": generated_payload,
                "warnings_payload": warnings_payload or None,
                "status": "review_pending" if warnings_payload else "draft",
            },
        )
        await self._create_audit_log(
            case_id=updated.case_id,
            entity_id=updated.id,
            action="generated_form_field_updated",
            actor_reference=payload.actor_reference,
            payload={
                "form_id": str(updated.form_id),
                "form_field_key": form_field_key,
                "manual_override": payload.manual_override,
            },
        )
        await self.session.commit()
        return await self.get_detail(updated.id)

    async def approve(
        self,
        generated_form_id: uuid.UUID,
        payload: GeneratedFormReviewRequest,
    ) -> GeneratedForm:
        generated_form = await self._get_generated_form(generated_form_id)
        await self._get_case(generated_form.case_id)
        if generated_form.status not in APPROVABLE_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="generated form cannot be approved")

        updated = await self.generated_form_repository.update(
            generated_form,
            {
                "status": "approved",
                "reviewed_by_user_id": payload.reviewed_by_user_id,
                "reviewed_at": datetime.now(UTC),
                "review_notes": payload.review_notes,
            },
        )
        updated.form = await self._get_form(updated.form_id)
        await self._create_audit_log(
            case_id=updated.case_id,
            entity_id=updated.id,
            action="generated_form_approved",
            actor_reference=payload.reviewed_by_user_id,
            payload={
                "form_id": str(updated.form_id),
                "draft_version": updated.draft_version,
            },
        )
        await self.session.commit()
        return updated

    async def mark_fix_required(
        self,
        generated_form_id: uuid.UUID,
        payload: GeneratedFormReviewRequest,
    ) -> GeneratedForm:
        generated_form = await self._get_generated_form(generated_form_id)
        await self._get_case(generated_form.case_id)
        if generated_form.status == "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="approved generated form cannot be modified",
            )

        updated = await self.generated_form_repository.update(
            generated_form,
            {
                "status": "fix_required",
                "reviewed_by_user_id": payload.reviewed_by_user_id,
                "reviewed_at": datetime.now(UTC),
                "review_notes": payload.review_notes,
            },
        )
        updated.form = await self._get_form(updated.form_id)
        await self._create_audit_log(
            case_id=updated.case_id,
            entity_id=updated.id,
            action="generated_form_fix_required",
            actor_reference=payload.reviewed_by_user_id,
            payload={
                "form_id": str(updated.form_id),
                "draft_version": updated.draft_version,
            },
        )
        await self.session.commit()
        return updated

    async def _get_case(self, case_id: uuid.UUID) -> Case:
        result = await self.session.execute(
            select(Case, Client)
            .join(Client, Case.client_id == Client.id)
            .where(Case.id == case_id)
        )
        row = result.first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
        case, client = row
        case.client = client
        return case

    async def _get_form(self, form_id: uuid.UUID) -> Form:
        form = await self.form_repository.get(form_id)
        if form is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="form not found")
        return form

    async def _get_generated_form(self, generated_form_id: uuid.UUID) -> GeneratedForm:
        generated_form = await self.generated_form_repository.get(generated_form_id)
        if generated_form is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="generated form not found")
        return generated_form

    def _build_form_payload(
        self,
        form: Form,
        mappings: list[FormFieldMapping],
        source_bundle: dict[str, Any],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        fields: dict[str, Any] = {}
        field_states: dict[str, dict[str, Any]] = {}
        warnings_payload: list[dict[str, Any]] = []

        for mapping in mappings:
            suggestions = self._build_suggestions(mapping, source_bundle)
            selected_suggestion = suggestions[0] if suggestions else None
            transformed_value = selected_suggestion.value if selected_suggestion is not None else None
            fields[mapping.form_field_key] = transformed_value
            field_states[mapping.form_field_key] = {
                "value": transformed_value,
                "manual_override": False,
                "selected_source_key": selected_suggestion.source_key if selected_suggestion else None,
                "selected_source_label": selected_suggestion.source_label if selected_suggestion else None,
            }
            warnings_payload.extend(self._build_field_warnings(mapping, transformed_value, suggestions))

        return (
            {
                "form_code": form.form_code,
                "form_name": form.form_name,
                "form_version": form.version,
                "fields": fields,
                "field_states": field_states,
            },
            warnings_payload,
        )

    def _apply_transform(
        self,
        raw_value: Any,
        transform_rule_json: dict[str, Any] | list[Any] | None,
    ) -> Any:
        if not isinstance(transform_rule_json, dict):
            return raw_value

        value = raw_value
        source_path = transform_rule_json.get("source_path")
        if source_path and isinstance(value, dict):
            value = self._extract_path_value(value, str(source_path))

        if self._is_missing_value(value) and "default_value" in transform_rule_json:
            value = transform_rule_json["default_value"]
        if transform_rule_json.get("uppercase") and isinstance(value, str):
            value = value.upper()
        if transform_rule_json.get("lowercase") and isinstance(value, str):
            value = value.lower()
        if "join_with" in transform_rule_json and isinstance(value, list):
            value = str(transform_rule_json["join_with"]).join(str(item) for item in value)
        if "boolean_to" in transform_rule_json and isinstance(value, bool):
            mapping = transform_rule_json["boolean_to"]
            if isinstance(mapping, dict):
                value = mapping.get(str(value).lower(), value)
        return value

    def _extract_path_value(self, value: dict[str, Any], source_path: str) -> Any:
        current: Any = value
        for part in source_path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    def _is_missing_value(self, value: Any) -> bool:
        return value is None or value == "" or value == [] or value == {}

    async def _build_source_bundle(self, case_id: uuid.UUID) -> dict[str, Any]:
        canonical_fields = await self.canonical_field_repository.list_for_case(case_id)
        documents = await self.document_repository.list_current_for_case(case_id)
        questionnaire_answers = await self.session.execute(
            select(QuestionnaireQuestion.key, QuestionnaireAnswer)
            .join(QuestionnaireAnswer, QuestionnaireAnswer.question_id == QuestionnaireQuestion.id)
            .where(QuestionnaireAnswer.case_id == case_id)
        )
        questionnaire_map = {
            key: answer
            for key, answer in questionnaire_answers.all()
        }
        return {
            "canonical_map": {field.field_key: field for field in canonical_fields},
            "documents": documents,
            "questionnaire_map": questionnaire_map,
        }

    def _build_suggestions(
        self,
        mapping: FormFieldMapping,
        source_bundle: dict[str, Any],
    ) -> list[GeneratedFormSuggestionRead]:
        suggestions: list[GeneratedFormSuggestionRead] = []
        canonical_map: dict[str, CaseCanonicalField] = source_bundle["canonical_map"]
        questionnaire_map: dict[str, QuestionnaireAnswer] = source_bundle["questionnaire_map"]
        documents: list[Document] = source_bundle["documents"]

        canonical_field = canonical_map.get(mapping.canonical_field_key)
        if canonical_field is not None:
            value = self._apply_transform(canonical_field.field_value, mapping.transform_rule_json)
            if not self._is_missing_value(value):
                suggestions.append(
                    GeneratedFormSuggestionRead(
                        source_type="canonical_field",
                        source_key=f"canonical:{canonical_field.field_key}",
                        source_label=f"Canonical field: {canonical_field.field_key}",
                        value=value,
                        confidence_score=float(canonical_field.confidence_score) if canonical_field.confidence_score is not None else None,
                        source_document_id=canonical_field.source_document_id,
                    )
                )

        questionnaire_answer = questionnaire_map.get(mapping.canonical_field_key)
        if questionnaire_answer is not None:
            raw_value = self._questionnaire_answer_value(questionnaire_answer)
            value = self._apply_transform(raw_value, mapping.transform_rule_json)
            if not self._is_missing_value(value):
                suggestions.append(
                    GeneratedFormSuggestionRead(
                        source_type="questionnaire_answer",
                        source_key=f"questionnaire:{mapping.canonical_field_key}",
                        source_label=f"Questionnaire: {mapping.canonical_field_key}",
                        value=value,
                    )
                )

        for document in documents:
            for raw_value in self._document_extracted_values(document, mapping):
                value = self._apply_transform(raw_value, mapping.transform_rule_json)
                if not self._is_missing_value(value):
                    suggestions.append(
                        GeneratedFormSuggestionRead(
                            source_type="document_extraction",
                            source_key=f"document:{document.id}:{mapping.canonical_field_key}",
                            source_label=f"Document extraction: {document.original_filename}",
                            value=value,
                            source_document_id=document.id,
                            source_document_name=document.original_filename,
                        )
                    )

        deduped: list[GeneratedFormSuggestionRead] = []
        seen: set[str] = set()
        for suggestion in suggestions:
            marker = f"{suggestion.source_type}|{suggestion.source_key}|{suggestion.value!r}"
            if marker in seen:
                continue
            seen.add(marker)
            deduped.append(suggestion)
        return deduped

    def _document_extracted_values(self, document: Document, mapping: FormFieldMapping) -> list[Any]:
        extracted = document.extracted_fields
        if not isinstance(extracted, dict):
            return []
        flattened = self._flatten_paths(extracted)
        lookup_keys = {
            mapping.canonical_field_key,
            str(mapping.transform_rule_json.get("source_path"))
            if isinstance(mapping.transform_rule_json, dict) and mapping.transform_rule_json.get("source_path")
            else None,
        }
        values = [flattened[key] for key in lookup_keys if key and key in flattened]
        return values

    def _flatten_paths(self, payload: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        flattened: dict[str, Any] = {}
        for key, value in payload.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                flattened.update(self._flatten_paths(value, path))
            else:
                flattened[path] = value
        return flattened

    def _questionnaire_answer_value(self, answer: QuestionnaireAnswer) -> Any:
        if answer.answer_boolean is not None:
            return answer.answer_boolean
        if answer.answer_choice is not None:
            return answer.answer_choice
        if answer.answer_choices is not None:
            return answer.answer_choices
        if answer.answer_date is not None:
            return answer.answer_date.isoformat()
        if answer.answer_json is not None:
            return answer.answer_json
        return answer.answer_text

    def _build_field_warnings(
        self,
        mapping: FormFieldMapping,
        current_value: Any,
        suggestions: list[GeneratedFormSuggestionRead],
    ) -> list[dict[str, Any]]:
        warnings: list[dict[str, Any]] = []
        if mapping.required and self._is_missing_value(current_value):
            warnings.append(
                {
                    "type": "missing_required_field",
                    "form_field_key": mapping.form_field_key,
                    "canonical_field_key": mapping.canonical_field_key,
                    "message": f"Required value for '{mapping.form_field_key}' is missing.",
                }
            )

        distinct_values = {
            repr(suggestion.value)
            for suggestion in suggestions
            if not self._is_missing_value(suggestion.value)
        }
        if len(distinct_values) > 1:
            warnings.append(
                {
                    "type": "conflicting_suggestions",
                    "form_field_key": mapping.form_field_key,
                    "canonical_field_key": mapping.canonical_field_key,
                    "message": f"Multiple suggestions conflict for '{mapping.form_field_key}'.",
                }
            )
        return warnings

    def _get_field_states(self, generated_form: GeneratedForm) -> dict[str, dict[str, Any]]:
        payload = generated_form.generated_payload if isinstance(generated_form.generated_payload, dict) else {}
        field_states = payload.get("field_states")
        return field_states if isinstance(field_states, dict) else {}

    def _rebuild_form_warnings(
        self,
        mappings: list[FormFieldMapping],
        field_states: dict[str, dict[str, Any]],
        source_bundle: dict[str, Any],
    ) -> list[dict[str, Any]]:
        warnings: list[dict[str, Any]] = []
        for mapping in mappings:
            suggestions = self._build_suggestions(mapping, source_bundle)
            current_value = field_states.get(mapping.form_field_key, {}).get("value")
            if current_value is None and suggestions:
                current_value = suggestions[0].value
            warnings.extend(self._build_field_warnings(mapping, current_value, suggestions))
        return warnings

    def _ensure_warning_list(self, payload: list[dict[str, Any]] | dict[str, Any] | None) -> list[dict[str, Any]]:
        if payload is None:
            return []
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            return [payload]
        return []

    def _humanize_key(self, key: str) -> str:
        suffix = key.split(".")[-1]
        return suffix.replace("_", " ").title()

    def _section_display_order(self, section_key: str) -> int:
        if section_key.startswith("part_"):
            try:
                return int(section_key.split("_", 1)[1])
            except (IndexError, ValueError):
                return 999
        return 999

    def _build_export_path(
        self,
        export_base_path: str | None,
        case: Case,
        form: Form,
        draft_version: int,
    ) -> str | None:
        if export_base_path is None:
            return None
        return f"{export_base_path.rstrip('/\\\\')}/{case.case_number}/{form.form_code}/draft-v{draft_version}.json"

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
                "entity_type": "generated_form",
                "entity_id": str(entity_id),
                "action": action,
                "actor_reference": actor_reference,
                "payload": payload,
                "occurred_at": datetime.now(UTC),
            }
        )
