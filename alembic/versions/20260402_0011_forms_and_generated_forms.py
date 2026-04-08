from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260402_0011"
down_revision = "20260402_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "forms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_type_id", sa.String(length=100), nullable=False),
        sa.Column("form_code", sa.String(length=100), nullable=False),
        sa.Column("form_name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_forms")),
    )
    op.create_index(op.f("ix_forms_case_type_id"), "forms", ["case_type_id"], unique=False)
    op.create_index(op.f("ix_forms_form_code"), "forms", ["form_code"], unique=False)
    op.create_index(op.f("ix_forms_is_active"), "forms", ["is_active"], unique=False)

    op.create_table(
        "form_field_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("form_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("form_field_key", sa.String(length=150), nullable=False),
        sa.Column("canonical_field_key", sa.String(length=150), nullable=False),
        sa.Column("transform_rule_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], name=op.f("fk_form_field_mappings_form_id_forms")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_field_mappings")),
    )
    op.create_index(op.f("ix_form_field_mappings_form_id"), "form_field_mappings", ["form_id"], unique=False)
    op.create_index(op.f("ix_form_field_mappings_form_field_key"), "form_field_mappings", ["form_field_key"], unique=False)
    op.create_index(op.f("ix_form_field_mappings_canonical_field_key"), "form_field_mappings", ["canonical_field_key"], unique=False)

    op.create_table(
        "generated_forms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("form_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("draft_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("generated_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("warnings_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("export_path", sa.String(length=500), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_generated_forms_case_id_cases")),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], name=op.f("fk_generated_forms_form_id_forms")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generated_forms")),
    )
    op.create_index(op.f("ix_generated_forms_case_id"), "generated_forms", ["case_id"], unique=False)
    op.create_index(op.f("ix_generated_forms_form_id"), "generated_forms", ["form_id"], unique=False)
    op.create_index(op.f("ix_generated_forms_status"), "generated_forms", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_generated_forms_status"), table_name="generated_forms")
    op.drop_index(op.f("ix_generated_forms_form_id"), table_name="generated_forms")
    op.drop_index(op.f("ix_generated_forms_case_id"), table_name="generated_forms")
    op.drop_table("generated_forms")

    op.drop_index(op.f("ix_form_field_mappings_canonical_field_key"), table_name="form_field_mappings")
    op.drop_index(op.f("ix_form_field_mappings_form_field_key"), table_name="form_field_mappings")
    op.drop_index(op.f("ix_form_field_mappings_form_id"), table_name="form_field_mappings")
    op.drop_table("form_field_mappings")

    op.drop_index(op.f("ix_forms_is_active"), table_name="forms")
    op.drop_index(op.f("ix_forms_form_code"), table_name="forms")
    op.drop_index(op.f("ix_forms_case_type_id"), table_name="forms")
    op.drop_table("forms")
