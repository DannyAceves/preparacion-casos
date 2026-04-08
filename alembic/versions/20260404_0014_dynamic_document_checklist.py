from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260404_0014"
down_revision = "20260404_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_checklist_templates",
        sa.Column("case_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_checklist_templates")),
    )
    op.create_index(
        op.f("ix_document_checklist_templates_case_type"),
        "document_checklist_templates",
        ["case_type"],
        unique=False,
    )

    op.create_table(
        "document_checklist_template_items",
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("default_applies", sa.Boolean(), nullable=False),
        sa.Column("color_required", sa.Boolean(), nullable=False),
        sa.Column("english_translation_required", sa.Boolean(), nullable=False),
        sa.Column("signed_copy_required", sa.Boolean(), nullable=False),
        sa.Column("original_required", sa.Boolean(), nullable=False),
        sa.Column("copy_only", sa.Boolean(), nullable=False),
        sa.Column("guidance", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["document_checklist_templates.id"],
            name=op.f("fk_document_checklist_template_items_template_id_document_checklist_templates"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_checklist_template_items")),
    )
    op.create_index(
        op.f("ix_document_checklist_template_items_document_type"),
        "document_checklist_template_items",
        ["document_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_checklist_template_items_template_id"),
        "document_checklist_template_items",
        ["template_id"],
        unique=False,
    )

    op.create_table(
        "case_document_checklist_items",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("applies", sa.Boolean(), nullable=False),
        sa.Column("requested", sa.Boolean(), nullable=False),
        sa.Column("received", sa.Boolean(), nullable=False),
        sa.Column("validated", sa.Boolean(), nullable=False),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("color_required", sa.Boolean(), nullable=False),
        sa.Column("english_translation_required", sa.Boolean(), nullable=False),
        sa.Column("signed_copy_required", sa.Boolean(), nullable=False),
        sa.Column("original_required", sa.Boolean(), nullable=False),
        sa.Column("copy_only", sa.Boolean(), nullable=False),
        sa.Column("is_manual", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_case_document_checklist_items_case_id_cases")),
        sa.ForeignKeyConstraint(
            ["template_item_id"],
            ["document_checklist_template_items.id"],
            name=op.f("fk_case_document_checklist_items_template_item_id_document_checklist_template_items"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_document_checklist_items")),
    )
    op.create_index(
        op.f("ix_case_document_checklist_items_case_id"),
        "case_document_checklist_items",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_document_checklist_items_document_type"),
        "case_document_checklist_items",
        ["document_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_document_checklist_items_template_item_id"),
        "case_document_checklist_items",
        ["template_item_id"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO document_checklist_templates (id, case_type, title, description)
        VALUES
          ('5c79b226-b63f-498e-9f0f-f6051e6f7f11', 'family-based', 'Family-Based Intake Checklist', 'Baseline family-based evidence requirements.'),
          ('0e6cc5e1-b456-4477-96e1-3ef72f18f15c', 'employment-based', 'Employment-Based Intake Checklist', 'Baseline employment-based evidence requirements.'),
          ('a430c642-bd9b-4c43-9786-b6da44f8d90d', 'humanitarian', 'Humanitarian Intake Checklist', 'Baseline humanitarian evidence requirements.')
        """
    )

    op.execute(
        """
        INSERT INTO document_checklist_template_items (
          id, template_id, label, document_type, display_order, default_applies,
          color_required, english_translation_required, signed_copy_required,
          original_required, copy_only, guidance
        )
        VALUES
          ('b498ea7f-62a1-43d8-8f44-d5ef1cda1e11', '5c79b226-b63f-498e-9f0f-f6051e6f7f11', 'Government-issued photo ID', 'photo-id', 0, true, true, false, false, false, true, 'Use a clear color copy of passport or state ID.'),
          ('9ed22f31-9032-4835-aeba-49a4e63b508d', '5c79b226-b63f-498e-9f0f-f6051e6f7f11', 'Marriage certificate', 'marriage-certificate', 1, true, true, true, false, false, true, 'Translation required if not in English.'),
          ('6ba5c321-6871-447b-aa9a-a15da31b34fa', '5c79b226-b63f-498e-9f0f-f6051e6f7f11', 'Joint financial evidence', 'joint-financial-evidence', 2, true, false, false, false, false, true, 'Statements covering the relevant filing period.'),
          ('4b1b7968-53b1-4b24-910a-45670097ca1d', '0e6cc5e1-b456-4477-96e1-3ef72f18f15c', 'Passport biographic page', 'passport-biographic-page', 0, true, true, false, false, false, true, 'Current passport copy for beneficiary.'),
          ('9c53a1d9-5311-4d2f-8f14-bb2159db0af8', '0e6cc5e1-b456-4477-96e1-3ef72f18f15c', 'Offer letter or support letter', 'employment-offer-letter', 1, true, false, false, true, false, false, 'Prefer signed employer support letter.'),
          ('34ea9f80-42cc-4413-92b1-a2f78ddd6bc7', '0e6cc5e1-b456-4477-96e1-3ef72f18f15c', 'Recent pay stubs', 'pay-stubs', 2, true, false, false, false, false, true, 'Last 3 to 6 months if available.'),
          ('84d661b7-1c60-4276-b753-b35c27b6dcb5', 'a430c642-bd9b-4c43-9786-b6da44f8d90d', 'Client declaration', 'client-declaration', 0, true, false, true, true, false, false, 'Signed declaration or affidavit.'),
          ('66dfb205-2e25-4f35-8880-cff57a8183c2', 'a430c642-bd9b-4c43-9786-b6da44f8d90d', 'Country conditions evidence', 'country-conditions-evidence', 1, true, true, false, false, false, true, 'Reports, articles or expert materials.'),
          ('98bf98b4-c516-4550-b539-94268d9c6d0f', 'a430c642-bd9b-4c43-9786-b6da44f8d90d', 'Identity and entry records', 'identity-entry-records', 2, true, true, true, false, false, true, 'Passport, visa, I-94 or alternate records.')
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_case_document_checklist_items_template_item_id"), table_name="case_document_checklist_items")
    op.drop_index(op.f("ix_case_document_checklist_items_document_type"), table_name="case_document_checklist_items")
    op.drop_index(op.f("ix_case_document_checklist_items_case_id"), table_name="case_document_checklist_items")
    op.drop_table("case_document_checklist_items")
    op.drop_index(op.f("ix_document_checklist_template_items_template_id"), table_name="document_checklist_template_items")
    op.drop_index(op.f("ix_document_checklist_template_items_document_type"), table_name="document_checklist_template_items")
    op.drop_table("document_checklist_template_items")
    op.drop_index(op.f("ix_document_checklist_templates_case_type"), table_name="document_checklist_templates")
    op.drop_table("document_checklist_templates")
