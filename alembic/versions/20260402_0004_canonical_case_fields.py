from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260402_0004"
down_revision = "20260402_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("case_canonical_fields", sa.Column("field_key", sa.String(length=150), nullable=True))
    op.add_column("case_canonical_fields", sa.Column("field_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("case_canonical_fields", sa.Column("source_priority", sa.Integer(), nullable=True))
    op.add_column("case_canonical_fields", sa.Column("status", sa.String(length=50), nullable=True))

    op.execute("UPDATE case_canonical_fields SET field_key = field_name WHERE field_key IS NULL")
    op.execute(
        "UPDATE case_canonical_fields "
        "SET field_value = COALESCE(field_value_json, to_jsonb(field_value_text)) "
        "WHERE field_value IS NULL"
    )
    op.execute("UPDATE case_canonical_fields SET source_priority = 0 WHERE source_priority IS NULL")
    op.execute("UPDATE case_canonical_fields SET status = 'suggested' WHERE status IS NULL")

    op.alter_column("case_canonical_fields", "field_key", nullable=False)
    op.alter_column("case_canonical_fields", "source_priority", nullable=False)
    op.alter_column("case_canonical_fields", "status", nullable=False)
    op.create_index(op.f("ix_case_canonical_fields_status"), "case_canonical_fields", ["status"], unique=False)
    op.create_unique_constraint(
        "uq_case_canonical_fields_case_id_field_key",
        "case_canonical_fields",
        ["case_id", "field_key"],
    )

    op.drop_index(op.f("ix_case_canonical_fields_field_name"), table_name="case_canonical_fields")
    op.drop_column("case_canonical_fields", "field_name")
    op.drop_column("case_canonical_fields", "field_value_text")
    op.drop_column("case_canonical_fields", "field_value_json")


def downgrade() -> None:
    op.add_column("case_canonical_fields", sa.Column("field_value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("case_canonical_fields", sa.Column("field_value_text", sa.Text(), nullable=True))
    op.add_column("case_canonical_fields", sa.Column("field_name", sa.String(length=150), nullable=True))

    op.execute("UPDATE case_canonical_fields SET field_name = field_key WHERE field_name IS NULL")
    op.execute(
        "UPDATE case_canonical_fields "
        "SET field_value_json = CASE WHEN jsonb_typeof(field_value) IN ('object', 'array') THEN field_value ELSE NULL END"
    )
    op.execute(
        "UPDATE case_canonical_fields "
        "SET field_value_text = CASE WHEN jsonb_typeof(field_value) = 'string' THEN trim(both '\"' from field_value::text) ELSE NULL END"
    )

    op.create_index(op.f("ix_case_canonical_fields_field_name"), "case_canonical_fields", ["field_name"], unique=False)
    op.drop_constraint("uq_case_canonical_fields_case_id_field_key", "case_canonical_fields", type_="unique")
    op.drop_index(op.f("ix_case_canonical_fields_status"), table_name="case_canonical_fields")
    op.drop_column("case_canonical_fields", "status")
    op.drop_column("case_canonical_fields", "source_priority")
    op.drop_column("case_canonical_fields", "field_value")
    op.drop_column("case_canonical_fields", "field_key")
    op.alter_column("case_canonical_fields", "field_name", nullable=False)
