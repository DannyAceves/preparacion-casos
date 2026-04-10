from app.services.roc_i751_defaults import (
    ROC_CHECKLIST_TEMPLATE,
    ROC_FORM_TEMPLATE,
    ROC_QUESTIONNAIRE_TEMPLATE,
    is_roc_i751_case_type,
    roc_i751_defaults_summary,
)


def test_roc_i751_aliases_are_recognized() -> None:
    assert is_roc_i751_case_type("roc-i751") is True
    assert is_roc_i751_case_type("I-751") is True
    assert is_roc_i751_case_type("removal-of-conditions") is True
    assert is_roc_i751_case_type("family-based") is False


def test_roc_i751_defaults_summary_reports_expected_sizes() -> None:
    summary = roc_i751_defaults_summary()

    assert summary["checklist_items"] >= 20
    assert summary["questionnaire_sections"] >= 6
    assert summary["questionnaire_questions"] >= 30
    assert summary["form_field_mappings"] >= 25


def test_roc_i751_checklist_document_types_are_unique() -> None:
    document_types = [
        item["document_type"]
        for item in ROC_CHECKLIST_TEMPLATE["items"]
        if item.get("document_type")
    ]

    assert len(document_types) == len(set(document_types))


def test_roc_i751_questionnaire_keys_are_unique() -> None:
    keys = [
        question["key"]
        for section in ROC_QUESTIONNAIRE_TEMPLATE["sections"]
        for question in section["questions"]
    ]

    assert len(keys) == len(set(keys))


def test_roc_i751_form_mappings_align_with_questionnaire_keys() -> None:
    questionnaire_keys = {
        question["key"]
        for section in ROC_QUESTIONNAIRE_TEMPLATE["sections"]
        for question in section["questions"]
    }
    mapping_keys = {
        mapping["canonical_field_key"]
        for mapping in ROC_FORM_TEMPLATE["mappings"]
    }

    assert "last_name" in mapping_keys
    assert "first_name" in mapping_keys
    assert "children" in mapping_keys
    assert mapping_keys.issubset(questionnaire_keys)
