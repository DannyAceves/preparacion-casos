from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260404_0017"
down_revision = "20260404_0016"
branch_labels = None
depends_on = None


FORM_ID = uuid.UUID("3a12ed2d-1c64-4be8-90bf-18c0a3e1f751")


def upgrade() -> None:
    op.add_column("form_field_mappings", sa.Column("section_key", sa.String(length=100), nullable=True))
    op.add_column("form_field_mappings", sa.Column("section_title", sa.String(length=255), nullable=True))
    op.add_column("form_field_mappings", sa.Column("field_label", sa.String(length=255), nullable=True))
    op.add_column("form_field_mappings", sa.Column("field_type", sa.String(length=50), nullable=True))
    op.add_column("form_field_mappings", sa.Column("help_text", sa.Text(), nullable=True))
    op.add_column(
        "form_field_mappings",
        sa.Column("display_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index(op.f("ix_form_field_mappings_section_key"), "form_field_mappings", ["section_key"], unique=False)
    op.create_index(op.f("ix_form_field_mappings_field_type"), "form_field_mappings", ["field_type"], unique=False)

    forms_table = sa.table(
        "forms",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("case_type_id", sa.String(length=100)),
        sa.column("form_code", sa.String(length=100)),
        sa.column("form_name", sa.String(length=255)),
        sa.column("version", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    mappings_table = sa.table(
        "form_field_mappings",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("form_id", postgresql.UUID(as_uuid=True)),
        sa.column("form_field_key", sa.String(length=150)),
        sa.column("canonical_field_key", sa.String(length=150)),
        sa.column("section_key", sa.String(length=100)),
        sa.column("section_title", sa.String(length=255)),
        sa.column("field_label", sa.String(length=255)),
        sa.column("field_type", sa.String(length=50)),
        sa.column("help_text", sa.Text()),
        sa.column("display_order", sa.Integer()),
        sa.column("transform_rule_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.column("required", sa.Boolean()),
    )

    connection = op.get_bind()
    has_family_i751 = connection.execute(
        sa.text(
            """
            select 1 from forms
            where case_type_id = :case_type_id and form_code = :form_code
            limit 1
            """
        ),
        {"case_type_id": "family-based", "form_code": "I-751"},
    ).scalar()

    if not has_family_i751:
        op.bulk_insert(
            forms_table,
            [
                {
                    "id": FORM_ID,
                    "case_type_id": "family-based",
                    "form_code": "I-751",
                    "form_name": "Petition to Remove Conditions on Residence",
                    "version": 1,
                    "is_active": True,
                }
            ],
        )

        op.bulk_insert(
            mappings_table,
            [
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1101"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_1.family_name",
                    "canonical_field_key": "last_name",
                    "section_key": "part_1",
                    "section_title": "Part 1. Information About You",
                    "field_label": "Family Name (Last Name)",
                    "field_type": "text",
                    "help_text": "Use the legal family name exactly as shown on identity documents.",
                    "display_order": 10,
                    "transform_rule_json": None,
                    "required": True,
                },
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1102"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_1.given_name",
                    "canonical_field_key": "first_name",
                    "section_key": "part_1",
                    "section_title": "Part 1. Information About You",
                    "field_label": "Given Name (First Name)",
                    "field_type": "text",
                    "help_text": "Use the applicant's current legal first name.",
                    "display_order": 20,
                    "transform_rule_json": None,
                    "required": True,
                },
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1103"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_1.middle_name",
                    "canonical_field_key": "middle_name",
                    "section_key": "part_1",
                    "section_title": "Part 1. Information About You",
                    "field_label": "Middle Name",
                    "field_type": "text",
                    "help_text": "Leave blank if no middle name exists.",
                    "display_order": 30,
                    "transform_rule_json": None,
                    "required": False,
                },
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1104"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_1.date_of_birth",
                    "canonical_field_key": "date_of_birth",
                    "section_key": "part_1",
                    "section_title": "Part 1. Information About You",
                    "field_label": "Date of Birth",
                    "field_type": "date",
                    "help_text": "Provide the date in the exact format used by the source document.",
                    "display_order": 40,
                    "transform_rule_json": None,
                    "required": True,
                },
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1105"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_1.a_number",
                    "canonical_field_key": "alien_registration_number",
                    "section_key": "part_1",
                    "section_title": "Part 1. Information About You",
                    "field_label": "A-Number",
                    "field_type": "text",
                    "help_text": "Include the A-number if available from documents or prior filings.",
                    "display_order": 50,
                    "transform_rule_json": None,
                    "required": False,
                },
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1106"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_2.marriage_date",
                    "canonical_field_key": "marriage_date",
                    "section_key": "part_2",
                    "section_title": "Part 2. Basis for Petition",
                    "field_label": "Date of Marriage",
                    "field_type": "date",
                    "help_text": "Use the official civil marriage date.",
                    "display_order": 60,
                    "transform_rule_json": None,
                    "required": True,
                },
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1107"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_2.joint_filing",
                    "canonical_field_key": "joint_filing",
                    "section_key": "part_2",
                    "section_title": "Part 2. Basis for Petition",
                    "field_label": "Joint Filing",
                    "field_type": "checkbox",
                    "help_text": "Mark yes when the petition is filed jointly with the spouse.",
                    "display_order": 70,
                    "transform_rule_json": None,
                    "required": True,
                },
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1108"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_3.spouse_family_name",
                    "canonical_field_key": "spouse_last_name",
                    "section_key": "part_3",
                    "section_title": "Part 3. Information About U.S. Citizen or Resident Spouse",
                    "field_label": "Spouse Family Name",
                    "field_type": "text",
                    "help_text": "Use the spouse's current legal family name.",
                    "display_order": 80,
                    "transform_rule_json": None,
                    "required": True,
                },
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1109"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_3.spouse_given_name",
                    "canonical_field_key": "spouse_first_name",
                    "section_key": "part_3",
                    "section_title": "Part 3. Information About U.S. Citizen or Resident Spouse",
                    "field_label": "Spouse Given Name",
                    "field_type": "text",
                    "help_text": "Use the spouse's current legal first name.",
                    "display_order": 90,
                    "transform_rule_json": None,
                    "required": True,
                },
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1110"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_3.spouse_date_of_birth",
                    "canonical_field_key": "spouse_date_of_birth",
                    "section_key": "part_3",
                    "section_title": "Part 3. Information About U.S. Citizen or Resident Spouse",
                    "field_label": "Spouse Date of Birth",
                    "field_type": "date",
                    "help_text": "Use the spouse's birth date exactly as documented.",
                    "display_order": 100,
                    "transform_rule_json": None,
                    "required": False,
                },
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1111"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_4.mailing_address",
                    "canonical_field_key": "mailing_address",
                    "section_key": "part_4",
                    "section_title": "Part 4. Address Information",
                    "field_label": "Mailing Address",
                    "field_type": "textarea",
                    "help_text": "Combine street, unit, city, state and ZIP if they are stored as a single canonical value.",
                    "display_order": 110,
                    "transform_rule_json": None,
                    "required": True,
                },
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1112"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_5.children",
                    "canonical_field_key": "children",
                    "section_key": "part_5",
                    "section_title": "Part 5. Information About Children",
                    "field_label": "Children Included With Petition",
                    "field_type": "repeatable_group",
                    "help_text": "Use one row per child when applicable.",
                    "display_order": 120,
                    "transform_rule_json": None,
                    "required": False,
                },
                {
                    "id": uuid.UUID("7f3a5ad1-b4e1-4ce4-93a7-ec37e8ab1113"),
                    "form_id": FORM_ID,
                    "form_field_key": "part_8.additional_information",
                    "canonical_field_key": "additional_information",
                    "section_key": "part_8",
                    "section_title": "Part 8. Additional Information",
                    "field_label": "Additional Information",
                    "field_type": "textarea",
                    "help_text": "Use this area for clarifications gathered from interview notes or follow-up review.",
                    "display_order": 130,
                    "transform_rule_json": None,
                    "required": False,
                },
            ],
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("delete from form_field_mappings where form_id = :form_id"),
        {"form_id": FORM_ID},
    )
    connection.execute(
        sa.text("delete from forms where id = :form_id"),
        {"form_id": FORM_ID},
    )

    op.drop_index(op.f("ix_form_field_mappings_field_type"), table_name="form_field_mappings")
    op.drop_index(op.f("ix_form_field_mappings_section_key"), table_name="form_field_mappings")
    op.drop_column("form_field_mappings", "display_order")
    op.drop_column("form_field_mappings", "help_text")
    op.drop_column("form_field_mappings", "field_type")
    op.drop_column("form_field_mappings", "field_label")
    op.drop_column("form_field_mappings", "section_title")
    op.drop_column("form_field_mappings", "section_key")
