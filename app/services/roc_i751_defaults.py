from __future__ import annotations

from tempfile import template
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document_checklist import (
    DocumentChecklistTemplate,
    DocumentChecklistTemplateItem,
)
from app.models.form import Form
from app.models.form_field_mapping import FormFieldMapping
from app.models.questionnaire_question import QuestionnaireQuestion
from app.models.questionnaire_section import QuestionnaireSection
from app.models.questionnaire_template import QuestionnaireTemplate

ROC_I751_CASE_TYPE_ALIASES = {
    "roc",
    "roc-i751",
    "i751",
    "i-751",
    "removal-of-conditions",
    "removal_of_conditions",
}


def is_roc_i751_case_type(case_type: str | None) -> bool:
    if case_type is None:
        return False
    normalized = case_type.strip().lower().replace(" ", "-")
    return normalized in ROC_I751_CASE_TYPE_ALIASES


ROC_CHECKLIST_TEMPLATE = {
    "title": "ROC Checklist Interview Template",
    "description": (
        "Interview-driven checklist for Removal of Conditions matters. "
        "Attorneys can mark what applies during the consultation, then the client portal can request and collect "
        "the selected evidence."
    ),
    "items": [
        {
            "label": "Conditional resident card (front and back copy)",
            "document_type": "conditional_resident_card",
            "default_applies": True,
            "copy_only": True,
            "guidance": "Request both sides of the permanent resident card.",
        },
        {
            "label": "Two passport-style photos of the conditional resident",
            "document_type": "conditional_resident_photos",
            "default_applies": True,
            "color_required": True,
            "original_required": True,
            "guidance": "Passport-style photos similar to the paper checklist.",
        },
        {
            "label": "Completed ROC questionnaire",
            "document_type": "roc_questionnaire",
            "default_applies": True,
            "guidance": "The client should complete the electronic questionnaire before packet assembly.",
        },
        {
            "label": "Proof of U.S. citizen or resident spouse status",
            "document_type": "spouse_status_evidence",
            "default_applies": True,
            "copy_only": True,
            "guidance": (
                "Any one of the following is sufficient: U.S. passport, naturalization certificate, "
                "or long-form birth certificate."
            ),
        },
        {
            "label": "Marriage certificate",
            "document_type": "marriage_certificate",
            "default_applies": True,
            "copy_only": True,
            "guidance": "Civil marriage certificate used to support the qualifying relationship.",
        },
        {
            "label": "Joint federal tax returns",
            "document_type": "joint_tax_returns",
            "default_applies": True,
            "copy_only": True,
            "guidance": "Prefer the most recent two years filed jointly when available.",
        },
        {
            "label": "W-2 or 1099 evidence for the U.S. citizen or resident spouse",
            "document_type": "spouse_income_evidence",
            "default_applies": True,
            "copy_only": True,
            "guidance": "Collect all available W-2s and 1099s tied to the relevant tax period.",
        },
        {
            "label": "Recent pay stubs",
            "document_type": "recent_pay_stubs",
            "default_applies": True,
            "copy_only": True,
            "guidance": "At least two recent pay statements from current employment.",
        },
        {
            "label": "Joint bank statements",
            "document_type": "joint_bank_statements",
            "default_applies": True,
            "copy_only": True,
            "guidance": "Five months minimum; longer history preferred.",
        },
        {
            "label": "Joint credit card statements",
            "document_type": "joint_credit_card_statements",
            "default_applies": False,
            "copy_only": True,
            "guidance": "Five months minimum; request only if the couple actually shares credit accounts.",
        },
        {
            "label": "Lease or mortgage showing both names",
            "document_type": "joint_housing_evidence",
            "default_applies": True,
            "copy_only": True,
            "signed_copy_required": True,
            "guidance": "Signed lease or ownership paperwork for a shared residence.",
        },
        {
            "label": "Utility or service bills in both names",
            "document_type": "joint_household_bills",
            "default_applies": False,
            "copy_only": True,
            "guidance": "Examples: electricity, water, internet, cable, cellular plan, or car insurance.",
        },
        {
            "label": "Vehicle purchase or insurance evidence in both names",
            "document_type": "joint_vehicle_evidence",
            "default_applies": False,
            "copy_only": True,
            "guidance": "Use if the couple jointly owns or insures a vehicle.",
        },
        {
            "label": "Birth certificates for children shared by the couple",
            "document_type": "children_birth_certificates",
            "default_applies": False,
            "copy_only": True,
            "guidance": "Include all children born to the conditional resident and petitioning spouse.",
        },
        {
            "label": "Pregnancy evidence",
            "document_type": "pregnancy_evidence",
            "default_applies": False,
            "copy_only": True,
            "guidance": "Use when the couple is expecting a child together.",
        },
        {
            "label": "Ten family or community photos with captions",
            "document_type": "relationship_photos",
            "default_applies": True,
            "copy_only": True,
            "guidance": "Caption each photo with who appears, where it was taken, and approximate date.",
        },
        {
            "label": "Social media evidence of the marriage",
            "document_type": "social_media_evidence",
            "default_applies": False,
            "copy_only": True,
            "guidance": "For example Facebook or other public relationship evidence.",
        },
        {
            "label": "Affidavits from friends or relatives",
            "document_type": "relationship_affidavits",
            "default_applies": False,
            "original_required": True,
            "guidance": (
                "Signed, notarized affidavits explaining how the writer knows the couple, with concrete examples "
                "and contact information."
            ),
        },
        {
            "label": "Proof of shared debts or financial support",
            "document_type": "shared_financial_obligations",
            "default_applies": False,
            "copy_only": True,
            "guidance": "Debts, money transfers, or other financial commingling evidence.",
        },
        {
            "label": "Divorce decree from a prior marriage",
            "document_type": "prior_divorce_decree",
            "default_applies": False,
            "copy_only": True,
            "guidance": "Only applies if the conditional resident or spouse had a prior marriage terminated by divorce.",
        },
        {
            "label": "Death certificate for prior spouse",
            "document_type": "prior_spouse_death_certificate",
            "default_applies": False,
            "copy_only": True,
            "guidance": "Only applies if a previous marriage ended because a spouse died.",
        },
        {
            "label": "Criminal case disposition or closure records",
            "document_type": "criminal_disposition_records",
            "default_applies": False,
            "copy_only": True,
            "guidance": "Only applies if the client reports arrest, detention, charge, or conviction history.",
        },
        {
            "label": "Child dependent resident card and birth certificate",
            "document_type": "child_dependent_identity_documents",
            "default_applies": False,
            "copy_only": True,
            "guidance": "Use when a child must file separately or be included as a dependent.",
        },
        {
            "label": "Two passport-style photos for each dependent child",
            "document_type": "child_dependent_photos",
            "default_applies": False,
            "color_required": True,
            "original_required": True,
            "guidance": "Only required when a dependent child is included.",
        },
    ],
}


ROC_QUESTIONNAIRE_TEMPLATE = {
    "title": "Removal of Conditions Questionnaire",
    "description": (
        "Electronic client questionnaire based on the ROC paper intake. It mirrors the information needed for "
        "I-751 preparation while reducing manual transcription errors."
    ),
    "sections": [
        {
            "title": "Part 1. Conditional Resident Information",
            "description": "Current identity, marital status, addresses, and core immigration history.",
            "questions": [
                {"key": "last_name", "prompt": "Family Name (Last Name)", "input_type": "text", "is_required": True},
                {"key": "first_name", "prompt": "Given Name (First Name)", "input_type": "text", "is_required": True},
                {"key": "middle_name", "prompt": "Middle Name", "input_type": "text", "is_required": False},
                {
                    "key": "other_names_used",
                    "prompt": "Other names used, including nicknames, aliases, and maiden name",
                    "input_type": "textarea",
                    "is_required": False,
                },
                {"key": "date_of_birth", "prompt": "Date of birth", "input_type": "date", "is_required": True},
                {"key": "country_of_birth", "prompt": "Country of birth", "input_type": "text", "is_required": True},
                {
                    "key": "country_of_citizenship",
                    "prompt": "Country of citizenship or nationality",
                    "input_type": "text",
                    "is_required": True,
                },
                {
                    "key": "alien_registration_number",
                    "prompt": "Alien Registration Number (A-Number)",
                    "input_type": "text",
                    "is_required": False,
                },
                {"key": "ssn", "prompt": "U.S. Social Security Number", "input_type": "text", "is_required": False},
                {
                    "key": "uscis_elis_account_number",
                    "prompt": "USCIS ELIS Account Number",
                    "input_type": "text",
                    "is_required": False,
                },
                {
                    "key": "marital_status",
                    "prompt": "Current marital status",
                    "input_type": "select",
                    "is_required": True,
                    "options": [
                        {"label": "Single", "value": "single"},
                        {"label": "Married", "value": "married"},
                        {"label": "Divorced", "value": "divorced"},
                        {"label": "Widowed", "value": "widowed"},
                    ],
                },
                {"key": "marriage_date", "prompt": "Date of marriage", "input_type": "date", "is_required": True},
                {"key": "marriage_place", "prompt": "Place of marriage", "input_type": "text", "is_required": True},
                {
                    "key": "marriage_end_date",
                    "prompt": "If the marriage ended, provide the date of divorce or death",
                    "input_type": "date",
                    "is_required": False,
                },
                {
                    "key": "conditional_residence_expires_on",
                    "prompt": "Conditional residence expiration date",
                    "input_type": "date",
                    "is_required": True,
                },
                {
                    "key": "mailing_address",
                    "prompt": "Mailing address",
                    "input_type": "textarea",
                    "is_required": True,
                    "help_text": "Include street, unit, city, state, ZIP, and any in-care-of line if applicable.",
                },
                {
                    "key": "physical_address_same_as_mailing",
                    "prompt": "Is your physical address the same as your mailing address?",
                    "input_type": "radio",
                    "is_required": True,
                    "options": [
                        {"label": "Yes", "value": "yes"},
                        {"label": "No", "value": "no"},
                    ],
                },
                {
                    "key": "physical_address",
                    "prompt": "Physical address, if different from mailing address",
                    "input_type": "textarea",
                    "is_required": False,
                },
                {
                    "key": "in_removal_proceedings",
                    "prompt": "Are you in removal, deportation, or rescission proceedings?",
                    "input_type": "radio",
                    "is_required": True,
                    "options": [
                        {"label": "Yes", "value": "yes"},
                        {"label": "No", "value": "no"},
                    ],
                },
                {
                    "key": "third_party_fee_paid",
                    "prompt": "Was a fee paid to anyone other than an attorney in connection with this petition?",
                    "input_type": "radio",
                    "is_required": True,
                    "options": [
                        {"label": "Yes", "value": "yes"},
                        {"label": "No", "value": "no"},
                    ],
                },
                {
                    "key": "arrest_history",
                    "prompt": (
                        "Have you ever been arrested, detained, charged, indicted, fined, imprisoned, or "
                        "committed a crime in the United States or abroad?"
                    ),
                    "input_type": "radio",
                    "is_required": True,
                    "options": [
                        {"label": "Yes", "value": "yes"},
                        {"label": "No", "value": "no"},
                    ],
                },
                {
                    "key": "arrest_history_explanation",
                    "prompt": "If yes, explain the arrest or criminal history in detail",
                    "input_type": "textarea",
                    "is_required": False,
                },
                {
                    "key": "different_marriage_basis",
                    "prompt": (
                        "If you are married, is this a different marriage than the one through which you gained "
                        "conditional resident status?"
                    ),
                    "input_type": "radio",
                    "is_required": True,
                    "options": [
                        {"label": "Yes", "value": "yes"},
                        {"label": "No", "value": "no"},
                    ],
                },
                {
                    "key": "prior_addresses_since_residence",
                    "prompt": "List all addresses where you have lived since becoming a permanent resident",
                    "input_type": "repeatable_group",
                    "is_required": False,
                    "field_config": {
                        "item_label": "Address",
                        "fields": ["from", "to", "street", "unit", "city", "county", "state", "zip"],
                    },
                },
                {
                    "key": "government_overseas_service",
                    "prompt": (
                        "Is your spouse or parent’s spouse currently serving with or employed by the U.S. Government "
                        "outside the United States?"
                    ),
                    "input_type": "radio",
                    "is_required": True,
                    "options": [
                        {"label": "Yes", "value": "yes"},
                        {"label": "No", "value": "no"},
                    ],
                },
            ],
        },
        {
            "title": "Part 2. Biographic Information",
            "description": "Biographic details needed for USCIS form preparation.",
            "questions": [
                {
                    "key": "ethnicity",
                    "prompt": "Ethnicity",
                    "input_type": "select",
                    "is_required": True,
                    "options": [
                        {"label": "Hispanic or Latino", "value": "hispanic_or_latino"},
                        {"label": "Not Hispanic or Latino", "value": "not_hispanic_or_latino"},
                    ],
                },
                {
                    "key": "race",
                    "prompt": "Race or races",
                    "input_type": "textarea",
                    "is_required": False,
                    "help_text": "List all that apply, separated by commas if needed.",
                },
                {"key": "height_feet", "prompt": "Height (feet)", "input_type": "text", "is_required": False},
                {"key": "height_inches", "prompt": "Height (inches)", "input_type": "text", "is_required": False},
                {"key": "weight_lbs", "prompt": "Weight (lbs)", "input_type": "text", "is_required": False},
                {
                    "key": "eye_color",
                    "prompt": "Eye color",
                    "input_type": "select",
                    "is_required": False,
                    "options": [
                        {"label": "Black", "value": "black"},
                        {"label": "Blue", "value": "blue"},
                        {"label": "Brown", "value": "brown"},
                        {"label": "Gray", "value": "gray"},
                        {"label": "Green", "value": "green"},
                        {"label": "Hazel", "value": "hazel"},
                        {"label": "Maroon", "value": "maroon"},
                        {"label": "Pink", "value": "pink"},
                        {"label": "Unknown or Other", "value": "unknown_other"},
                    ],
                },
                {
                    "key": "hair_color",
                    "prompt": "Hair color",
                    "input_type": "select",
                    "is_required": False,
                    "options": [
                        {"label": "Bald", "value": "bald"},
                        {"label": "Black", "value": "black"},
                        {"label": "Blond", "value": "blond"},
                        {"label": "Brown", "value": "brown"},
                        {"label": "Gray", "value": "gray"},
                        {"label": "Red", "value": "red"},
                        {"label": "Sandy", "value": "sandy"},
                        {"label": "White", "value": "white"},
                        {"label": "Unknown or Other", "value": "unknown_other"},
                    ],
                },
            ],
        },
        {
            "title": "Part 3. Basis for Petition",
            "description": "Joint filing or waiver basis for the I-751 filing.",
            "questions": [
                {
                    "key": "joint_filing_party",
                    "prompt": "If filing jointly, who are you filing with?",
                    "input_type": "select",
                    "is_required": False,
                    "options": [
                        {"label": "My spouse", "value": "spouse"},
                        {"label": "My parent's spouse", "value": "parents_spouse"},
                    ],
                },
                {
                    "key": "waiver_basis",
                    "prompt": "If you cannot file jointly, explain the waiver basis",
                    "input_type": "textarea",
                    "is_required": False,
                    "help_text": "Examples: spouse deceased, divorce, battery or extreme cruelty, or extreme hardship.",
                },
            ],
        },
        {
            "title": "Part 4. U.S. Citizen or Resident Spouse Information",
            "description": "Identity and address details for the petitioning spouse or stepparent.",
            "questions": [
                {
                    "key": "spouse_relationship",
                    "prompt": "Relationship to the qualifying relative",
                    "input_type": "select",
                    "is_required": True,
                    "options": [
                        {"label": "Spouse or former spouse", "value": "spouse"},
                        {"label": "Parent's spouse or former spouse", "value": "parents_spouse"},
                    ],
                },
                {"key": "spouse_last_name", "prompt": "Spouse family name", "input_type": "text", "is_required": True},
                {"key": "spouse_first_name", "prompt": "Spouse given name", "input_type": "text", "is_required": True},
                {"key": "spouse_middle_name", "prompt": "Spouse middle name", "input_type": "text", "is_required": False},
                {"key": "spouse_date_of_birth", "prompt": "Spouse date of birth", "input_type": "date", "is_required": False},
                {"key": "spouse_ssn", "prompt": "Spouse U.S. Social Security Number", "input_type": "text", "is_required": False},
                {"key": "spouse_a_number", "prompt": "Spouse A-Number", "input_type": "text", "is_required": False},
                {
                    "key": "spouse_physical_address",
                    "prompt": "Spouse physical address",
                    "input_type": "textarea",
                    "is_required": False,
                },
            ],
        },
        {
            "title": "Part 5. Children",
            "description": "All children of the conditional resident, regardless of age.",
            "questions": [
                {
                    "key": "children",
                    "prompt": "List all children",
                    "input_type": "repeatable_group",
                    "is_required": False,
                    "field_config": {
                        "item_label": "Child",
                        "fields": ["full_name", "date_of_birth", "a_number", "living_with_you", "applying_with_you", "address"],
                    },
                }
            ],
        },
        {
            "title": "Part 6. Accommodations",
            "description": "Disability or impairment accommodations requested for USCIS interactions.",
            "questions": [
                {
                    "key": "accommodation_requested_self",
                    "prompt": "Are you requesting an accommodation because of your disabilities or impairments?",
                    "input_type": "radio",
                    "is_required": True,
                    "options": [
                        {"label": "Yes", "value": "yes"},
                        {"label": "No", "value": "no"},
                    ],
                },
                {
                    "key": "accommodation_requested_spouse",
                    "prompt": "Is your spouse requesting an accommodation because of disabilities or impairments?",
                    "input_type": "radio",
                    "is_required": True,
                    "options": [
                        {"label": "Yes", "value": "yes"},
                        {"label": "No", "value": "no"},
                    ],
                },
                {
                    "key": "accommodation_requested_children",
                    "prompt": "Are included children requesting accommodations because of disabilities or impairments?",
                    "input_type": "radio",
                    "is_required": True,
                    "options": [
                        {"label": "Yes", "value": "yes"},
                        {"label": "No", "value": "no"},
                    ],
                },
                {
                    "key": "accommodation_details",
                    "prompt": "Describe the accommodations requested",
                    "input_type": "textarea",
                    "is_required": False,
                },
            ],
        },
        {
            "title": "Part 7. Language and Review",
            "description": "Language access and signature preparation details.",
            "questions": [
                {
                    "key": "petitioner_can_read_english",
                    "prompt": "Can the petitioner read and understand English?",
                    "input_type": "radio",
                    "is_required": True,
                    "options": [
                        {"label": "Yes", "value": "yes"},
                        {"label": "No", "value": "no"},
                    ],
                },
                {
                    "key": "beneficiary_can_read_english",
                    "prompt": "Can the beneficiary read and understand English?",
                    "input_type": "radio",
                    "is_required": True,
                    "options": [
                        {"label": "Yes", "value": "yes"},
                        {"label": "No", "value": "no"},
                    ],
                },
                {
                    "key": "additional_information",
                    "prompt": "Additional information or clarifications for legal review",
                    "input_type": "textarea",
                    "is_required": False,
                },
            ],
        },
    ],
}


ROC_FORM_TEMPLATE = {
    "form_code": "I-751",
    "form_name": "Petition to Remove Conditions on Residence",
    "version": 1,
    "mappings": [
        {"form_field_key": "part_1.family_name", "canonical_field_key": "last_name", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Family Name (Last Name)", "field_type": "text", "required": True, "display_order": 10},
        {"form_field_key": "part_1.given_name", "canonical_field_key": "first_name", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Given Name (First Name)", "field_type": "text", "required": True, "display_order": 20},
        {"form_field_key": "part_1.middle_name", "canonical_field_key": "middle_name", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Middle Name", "field_type": "text", "required": False, "display_order": 30},
        {"form_field_key": "part_1.other_names_used", "canonical_field_key": "other_names_used", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Other Names Used", "field_type": "textarea", "required": False, "display_order": 40},
        {"form_field_key": "part_1.date_of_birth", "canonical_field_key": "date_of_birth", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Date of Birth", "field_type": "date", "required": True, "display_order": 50},
        {"form_field_key": "part_1.country_of_birth", "canonical_field_key": "country_of_birth", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Country of Birth", "field_type": "text", "required": True, "display_order": 60},
        {"form_field_key": "part_1.country_of_citizenship", "canonical_field_key": "country_of_citizenship", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Country of Citizenship or Nationality", "field_type": "text", "required": True, "display_order": 70},
        {"form_field_key": "part_1.a_number", "canonical_field_key": "alien_registration_number", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "A-Number", "field_type": "text", "required": False, "display_order": 80},
        {"form_field_key": "part_1.ssn", "canonical_field_key": "ssn", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "U.S. Social Security Number", "field_type": "text", "required": False, "display_order": 90},
        {"form_field_key": "part_1.elis_account_number", "canonical_field_key": "uscis_elis_account_number", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "USCIS ELIS Account Number", "field_type": "text", "required": False, "display_order": 100},
        {"form_field_key": "part_1.marital_status", "canonical_field_key": "marital_status", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Current Marital Status", "field_type": "text", "required": True, "display_order": 110},
        {"form_field_key": "part_1.marriage_date", "canonical_field_key": "marriage_date", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Date of Marriage", "field_type": "date", "required": True, "display_order": 120},
        {"form_field_key": "part_1.marriage_place", "canonical_field_key": "marriage_place", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Place of Marriage", "field_type": "text", "required": True, "display_order": 130},
        {"form_field_key": "part_1.marriage_end_date", "canonical_field_key": "marriage_end_date", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Date Marriage Ended", "field_type": "date", "required": False, "display_order": 140},
        {"form_field_key": "part_1.conditional_residence_expires_on", "canonical_field_key": "conditional_residence_expires_on", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Conditional Residence Expires On", "field_type": "date", "required": True, "display_order": 150},
        {"form_field_key": "part_1.mailing_address", "canonical_field_key": "mailing_address", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Mailing Address", "field_type": "textarea", "required": True, "display_order": 160},
        {"form_field_key": "part_1.physical_address", "canonical_field_key": "physical_address", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Physical Address", "field_type": "textarea", "required": False, "display_order": 170},
        {"form_field_key": "part_1.in_removal_proceedings", "canonical_field_key": "in_removal_proceedings", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "In Removal Proceedings", "field_type": "text", "required": True, "display_order": 180},
        {"form_field_key": "part_1.arrest_history", "canonical_field_key": "arrest_history", "section_key": "part_1", "section_title": "Part 1. Information About You", "field_label": "Arrest or Criminal History", "field_type": "text", "required": True, "display_order": 190},
        {"form_field_key": "part_2.joint_filing_party", "canonical_field_key": "joint_filing_party", "section_key": "part_2", "section_title": "Part 2. Basis for Petition", "field_label": "Joint Filing Party", "field_type": "text", "required": False, "display_order": 200},
        {"form_field_key": "part_2.waiver_basis", "canonical_field_key": "waiver_basis", "section_key": "part_2", "section_title": "Part 2. Basis for Petition", "field_label": "Waiver Basis", "field_type": "textarea", "required": False, "display_order": 210},
        {"form_field_key": "part_3.spouse_relationship", "canonical_field_key": "spouse_relationship", "section_key": "part_3", "section_title": "Part 3. Information About Qualifying Relative", "field_label": "Relationship", "field_type": "text", "required": True, "display_order": 220},
        {"form_field_key": "part_3.spouse_family_name", "canonical_field_key": "spouse_last_name", "section_key": "part_3", "section_title": "Part 3. Information About Qualifying Relative", "field_label": "Spouse Family Name", "field_type": "text", "required": True, "display_order": 230},
        {"form_field_key": "part_3.spouse_given_name", "canonical_field_key": "spouse_first_name", "section_key": "part_3", "section_title": "Part 3. Information About Qualifying Relative", "field_label": "Spouse Given Name", "field_type": "text", "required": True, "display_order": 240},
        {"form_field_key": "part_3.spouse_middle_name", "canonical_field_key": "spouse_middle_name", "section_key": "part_3", "section_title": "Part 3. Information About Qualifying Relative", "field_label": "Spouse Middle Name", "field_type": "text", "required": False, "display_order": 250},
        {"form_field_key": "part_3.spouse_date_of_birth", "canonical_field_key": "spouse_date_of_birth", "section_key": "part_3", "section_title": "Part 3. Information About Qualifying Relative", "field_label": "Spouse Date of Birth", "field_type": "date", "required": False, "display_order": 260},
        {"form_field_key": "part_3.spouse_ssn", "canonical_field_key": "spouse_ssn", "section_key": "part_3", "section_title": "Part 3. Information About Qualifying Relative", "field_label": "Spouse SSN", "field_type": "text", "required": False, "display_order": 270},
        {"form_field_key": "part_3.spouse_a_number", "canonical_field_key": "spouse_a_number", "section_key": "part_3", "section_title": "Part 3. Information About Qualifying Relative", "field_label": "Spouse A-Number", "field_type": "text", "required": False, "display_order": 280},
        {"form_field_key": "part_3.spouse_physical_address", "canonical_field_key": "spouse_physical_address", "section_key": "part_3", "section_title": "Part 3. Information About Qualifying Relative", "field_label": "Spouse Physical Address", "field_type": "textarea", "required": False, "display_order": 290},
        {"form_field_key": "part_5.children", "canonical_field_key": "children", "section_key": "part_5", "section_title": "Part 5. Information About Children", "field_label": "Children", "field_type": "repeatable_group", "required": False, "display_order": 300},
        {"form_field_key": "part_6.accommodation_requested_self", "canonical_field_key": "accommodation_requested_self", "section_key": "part_6", "section_title": "Part 6. Accommodations", "field_label": "Accommodation Requested for Self", "field_type": "text", "required": True, "display_order": 310},
        {"form_field_key": "part_6.accommodation_requested_spouse", "canonical_field_key": "accommodation_requested_spouse", "section_key": "part_6", "section_title": "Part 6. Accommodations", "field_label": "Accommodation Requested for Spouse", "field_type": "text", "required": True, "display_order": 320},
        {"form_field_key": "part_6.accommodation_requested_children", "canonical_field_key": "accommodation_requested_children", "section_key": "part_6", "section_title": "Part 6. Accommodations", "field_label": "Accommodation Requested for Children", "field_type": "text", "required": True, "display_order": 330},
        {"form_field_key": "part_6.accommodation_details", "canonical_field_key": "accommodation_details", "section_key": "part_6", "section_title": "Part 6. Accommodations", "field_label": "Accommodation Details", "field_type": "textarea", "required": False, "display_order": 340},
        {"form_field_key": "part_7.petitioner_can_read_english", "canonical_field_key": "petitioner_can_read_english", "section_key": "part_7", "section_title": "Part 7. Language and Review", "field_label": "Petitioner Can Read English", "field_type": "text", "required": True, "display_order": 350},
        {"form_field_key": "part_7.beneficiary_can_read_english", "canonical_field_key": "beneficiary_can_read_english", "section_key": "part_7", "section_title": "Part 7. Language and Review", "field_label": "Beneficiary Can Read English", "field_type": "text", "required": True, "display_order": 360},
        {"form_field_key": "part_8.additional_information", "canonical_field_key": "additional_information", "section_key": "part_8", "section_title": "Part 8. Additional Information", "field_label": "Additional Information", "field_type": "textarea", "required": False, "display_order": 370},
    ],
}


async def ensure_roc_i751_defaults(session: AsyncSession, case_type: str | None) -> None:
    if not is_roc_i751_case_type(case_type):
        return
    assert case_type is not None
    await _ensure_checklist_template(session, case_type)
    await _ensure_questionnaire_template(session, case_type)
    await _ensure_i751_form(session, case_type)


async def _ensure_checklist_template(session: AsyncSession, case_type: str) -> None:
    result = await session.execute(
        select(DocumentChecklistTemplate)
        .options(selectinload(DocumentChecklistTemplate.items))
        .where(DocumentChecklistTemplate.case_type == case_type)
    )
    template = result.scalar_one_or_none()

    if template is None:
        template = DocumentChecklistTemplate(
            case_type=case_type,
            title=ROC_CHECKLIST_TEMPLATE["title"],
            description=ROC_CHECKLIST_TEMPLATE["description"],
        )
        session.add(template)
        await session.flush()
        existing_keys: set[tuple[str, str]] = set()
    else:
        existing_keys = {
            ((item.document_type or "").strip().lower(), item.label.strip().lower())
            for item in template.items
        }

    for index, item in enumerate(ROC_CHECKLIST_TEMPLATE["items"], start=1):
        item_key = (
            ((item.get("document_type") or "").strip().lower()),
            item["label"].strip().lower(),
        )
        if item_key in existing_keys:
            continue

        session.add(
            DocumentChecklistTemplateItem(
                template_id=template.id,
                label=item["label"],
                document_type=item.get("document_type"),
                display_order=index,
                default_applies=bool(item.get("default_applies", True)),
                color_required=bool(item.get("color_required", False)),
                english_translation_required=bool(item.get("english_translation_required", False)),
                signed_copy_required=bool(item.get("signed_copy_required", False)),
                original_required=bool(item.get("original_required", False)),
                copy_only=bool(item.get("copy_only", False)),
                guidance=item.get("guidance"),
            )
        )

    await session.flush()

async def _ensure_questionnaire_template(session: AsyncSession, case_type: str) -> None:
    result = await session.execute(
        select(QuestionnaireTemplate)
        .options(
            selectinload(QuestionnaireTemplate.sections).selectinload(QuestionnaireSection.questions),
        )
        .where(
            QuestionnaireTemplate.case_type == case_type,
            QuestionnaireTemplate.status == "active",
        )
        .order_by(QuestionnaireTemplate.version.desc())
    )
    template = result.scalars().first()
    existing_sections: list[QuestionnaireSection] = []
    if template is None:
        template = QuestionnaireTemplate(
            case_type=case_type,
            title=ROC_QUESTIONNAIRE_TEMPLATE["title"],
            description=ROC_QUESTIONNAIRE_TEMPLATE["description"],
            status="active",
            version=1,
        )
        session.add(template)
        await session.flush()
    else:
        existing_sections = list(template.sections)

    section_map = {section.title.strip().lower(): section for section in existing_sections}
    for section_index, section_data in enumerate(ROC_QUESTIONNAIRE_TEMPLATE["sections"], start=1):
        section = section_map.get(section_data["title"].strip().lower())
        if section is None:
            section = QuestionnaireSection(
                template_id=template.id,
                title=section_data["title"],
                description=section_data.get("description"),
                display_order=section_index,
            )
            session.add(section)
            await session.flush()
            question_keys: set[str] = set()
        else:
            question_keys = {question.key for question in section.questions}
        for question_index, question_data in enumerate(section_data["questions"], start=1):
            if question_data["key"] in question_keys:
                continue
            session.add(
                QuestionnaireQuestion(
                    section_id=section.id,
                    key=question_data["key"],
                    prompt=question_data["prompt"],
                    help_text=question_data.get("help_text"),
                    input_type=question_data["input_type"],
                    is_required=bool(question_data.get("is_required", False)),
                    display_order=question_index,
                    options=question_data.get("options"),
                    validation_rules=question_data.get("validation_rules"),
                    conditional_rules=question_data.get("conditional_rules"),
                    field_config=question_data.get("field_config"),
                )
            )
            question_keys.add(question_data["key"])
    await session.flush()


async def _ensure_i751_form(session: AsyncSession, case_type: str) -> None:
    result = await session.execute(
        select(Form)
        .options(selectinload(Form.field_mappings))
        .where(
            Form.case_type_id == case_type,
            Form.form_code == ROC_FORM_TEMPLATE["form_code"],
            Form.is_active.is_(True),
        )
        .order_by(Form.version.desc())
    )
    form = result.scalars().first()
    existing_field_keys: set[str] = set()
    if form is None:
        form = Form(
            case_type_id=case_type,
            form_code=ROC_FORM_TEMPLATE["form_code"],
            form_name=ROC_FORM_TEMPLATE["form_name"],
            version=ROC_FORM_TEMPLATE["version"],
            is_active=True,
        )
        session.add(form)
        await session.flush()
    else:
        existing_field_keys = {mapping.form_field_key for mapping in form.field_mappings}
    for mapping in ROC_FORM_TEMPLATE["mappings"]:
        if mapping["form_field_key"] in existing_field_keys:
            continue
        session.add(
            FormFieldMapping(
                form_id=form.id,
                form_field_key=mapping["form_field_key"],
                canonical_field_key=mapping["canonical_field_key"],
                section_key=mapping.get("section_key"),
                section_title=mapping.get("section_title"),
                field_label=mapping.get("field_label"),
                field_type=mapping.get("field_type"),
                help_text=mapping.get("help_text"),
                display_order=int(mapping.get("display_order", 0)),
                transform_rule_json=mapping.get("transform_rule_json"),
                required=bool(mapping.get("required", False)),
            )
        )
        existing_field_keys.add(mapping["form_field_key"])
    await session.flush()


def roc_i751_defaults_summary() -> dict[str, Any]:
    return {
        "checklist_items": len(ROC_CHECKLIST_TEMPLATE["items"]),
        "questionnaire_sections": len(ROC_QUESTIONNAIRE_TEMPLATE["sections"]),
        "questionnaire_questions": sum(
            len(section["questions"]) for section in ROC_QUESTIONNAIRE_TEMPLATE["sections"]
        ),
        "form_field_mappings": len(ROC_FORM_TEMPLATE["mappings"]),
    }
