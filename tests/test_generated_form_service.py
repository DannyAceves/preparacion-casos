from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.generated_form import GenerateFormsRequest, GeneratedFormReviewRequest
from app.services.generated_form import GeneratedFormService


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class FakeSession:
    committed: bool = False

    async def commit(self) -> None:
        self.committed = True


@dataclass
class FakeFormRepository:
    forms_by_case_type: dict[str, list[object]]
    forms_by_id: dict[uuid.UUID, object]

    async def list_active_for_case_type(self, case_type_id: str) -> list[object]:
        return self.forms_by_case_type.get(case_type_id, [])

    async def get(self, form_id: uuid.UUID) -> object | None:
        return self.forms_by_id.get(form_id)


@dataclass
class FakeMappingRepository:
    mappings_by_form_id: dict[uuid.UUID, list[object]]

    async def list_for_form(self, form_id: uuid.UUID) -> list[object]:
        return self.mappings_by_form_id.get(form_id, [])


@dataclass
class FakeGeneratedFormRepository:
    items: list[object] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        entity = SimpleNamespace(id=uuid.uuid4(), created_at=_now(), updated_at=_now(), **data)
        self.items.append(entity)
        return entity

    async def list_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [item for item in self.items if item.case_id == case_id]

    async def get_latest_draft_version(self, case_id: uuid.UUID, form_id: uuid.UUID) -> int:
        drafts = [item for item in self.items if item.case_id == case_id and item.form_id == form_id]
        drafts.sort(key=lambda item: item.draft_version, reverse=True)
        return drafts[0].draft_version if drafts else 0

    async def get(self, generated_form_id: uuid.UUID) -> object | None:
        for item in self.items:
            if item.id == generated_form_id:
                return item
        return None

    async def update(self, entity: object, data: dict) -> object:
        for key, value in data.items():
            setattr(entity, key, value)
        entity.updated_at = _now()
        return entity


@dataclass
class FakeCanonicalFieldRepository:
    items: list[object]

    async def list_for_case(self, case_id: uuid.UUID) -> list[object]:
        return [item for item in self.items if item.case_id == case_id]


@dataclass
class FakeAuditLogRepository:
    items: list[dict] = field(default_factory=list)

    async def create(self, data: dict) -> object:
        self.items.append(data)
        return SimpleNamespace(**data)


def build_fixture() -> tuple[uuid.UUID, GeneratedFormService]:
    case_id = uuid.uuid4()
    form_id = uuid.uuid4()
    form = SimpleNamespace(id=form_id, case_type_id="family-based", form_code="I-130", form_name="Petition", version=1)
    mappings = [
        SimpleNamespace(
            form_id=form_id,
            form_field_key="beneficiary.full_name",
            canonical_field_key="beneficiary.full_name",
            transform_rule_json={"uppercase": True},
            required=True,
        ),
        SimpleNamespace(
            form_id=form_id,
            form_field_key="beneficiary.birth_date",
            canonical_field_key="beneficiary.birth_date",
            transform_rule_json=None,
            required=True,
        ),
    ]
    service = GeneratedFormService(FakeSession())
    service.form_repository = FakeFormRepository({"family-based": [form]}, {form_id: form})
    service.mapping_repository = FakeMappingRepository({form_id: mappings})
    service.generated_form_repository = FakeGeneratedFormRepository()
    service.canonical_field_repository = FakeCanonicalFieldRepository(
        [
            SimpleNamespace(
                case_id=case_id,
                field_key="beneficiary.full_name",
                field_value="Demo Applicant",
                confidence_score=Decimal("0.98"),
            )
        ]
    )
    service.audit_log_repository = FakeAuditLogRepository()

    case = SimpleNamespace(id=case_id, case_type="family-based", case_number="CASE-001")

    async def fake_get_case(incoming_case_id: uuid.UUID):
        if incoming_case_id != case_id:
            raise HTTPException(status_code=404, detail="case not found")
        return case

    service._get_case = fake_get_case
    return case_id, service


@pytest.mark.asyncio
async def test_generate_forms_creates_review_pending_when_required_field_missing() -> None:
    case_id, service = build_fixture()

    generated_forms = await service.generate_for_case(
        case_id,
        GenerateFormsRequest(generated_by_reference="paralegal-1", export_base_path="/tmp/forms"),
    )

    assert len(generated_forms) == 1
    assert generated_forms[0].status == "review_pending"
    assert generated_forms[0].generated_payload["fields"]["beneficiary.full_name"] == "DEMO APPLICANT"
    assert generated_forms[0].warnings_payload[0]["type"] == "missing_required_field"
    assert generated_forms[0].export_path.endswith("/CASE-001/I-130/draft-v1.json")
    assert service.audit_log_repository.items[0]["action"] == "generated_form_created"


@pytest.mark.asyncio
async def test_approve_generated_form_updates_review_metadata() -> None:
    case_id, service = build_fixture()
    generated = (await service.generate_for_case(case_id, GenerateFormsRequest()))[0]

    approved = await service.approve(
        generated.id,
        GeneratedFormReviewRequest(reviewed_by_user_id="attorney-1", review_notes="Looks good"),
    )

    assert approved.status == "approved"
    assert approved.reviewed_by_user_id == "attorney-1"
    assert service.audit_log_repository.items[-1]["action"] == "generated_form_approved"


@pytest.mark.asyncio
async def test_mark_fix_required_rejects_approved_form() -> None:
    case_id, service = build_fixture()
    generated = (await service.generate_for_case(case_id, GenerateFormsRequest()))[0]
    await service.approve(generated.id, GeneratedFormReviewRequest(reviewed_by_user_id="attorney-1"))

    with pytest.raises(HTTPException) as exc_info:
        await service.mark_fix_required(
            generated.id,
            GeneratedFormReviewRequest(reviewed_by_user_id="qa-1", review_notes="Needs corrections"),
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_generated_form_detail_returns_template_metadata() -> None:
    case_id, service = build_fixture()
    generated = (await service.generate_for_case(case_id, GenerateFormsRequest()))[0]

    detail = await service.get_detail(generated.id)

    assert detail.form.form_code == "I-130"
    assert detail.case_id == case_id
