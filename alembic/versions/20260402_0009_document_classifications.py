from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260402_0009"
down_revision = "20260402_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("classification_confidence_score", sa.Float(), nullable=True))
    op.create_table(
        "document_classifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("predicted_type", sa.String(length=100), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("classification_source", sa.String(length=50), nullable=False),
        sa.Column("classification_method", sa.String(length=100), nullable=False),
        sa.Column("is_override", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("reviewed_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("evidence_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_document_classifications_case_id_cases")),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_document_classifications_document_id_documents")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_classifications")),
    )
    op.create_index(op.f("ix_document_classifications_case_id"), "document_classifications", ["case_id"], unique=False)
    op.create_index(op.f("ix_document_classifications_document_id"), "document_classifications", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_classifications_predicted_type"), "document_classifications", ["predicted_type"], unique=False)
    op.create_index(op.f("ix_document_classifications_classification_source"), "document_classifications", ["classification_source"], unique=False)
    op.create_index(op.f("ix_document_classifications_is_override"), "document_classifications", ["is_override"], unique=False)
    op.create_index(op.f("ix_document_classifications_is_active"), "document_classifications", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_classifications_is_active"), table_name="document_classifications")
    op.drop_index(op.f("ix_document_classifications_is_override"), table_name="document_classifications")
    op.drop_index(op.f("ix_document_classifications_classification_source"), table_name="document_classifications")
    op.drop_index(op.f("ix_document_classifications_predicted_type"), table_name="document_classifications")
    op.drop_index(op.f("ix_document_classifications_document_id"), table_name="document_classifications")
    op.drop_index(op.f("ix_document_classifications_case_id"), table_name="document_classifications")
    op.drop_table("document_classifications")
    op.drop_column("documents", "classification_confidence_score")
