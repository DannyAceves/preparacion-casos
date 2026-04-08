from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260402_0007"
down_revision = "20260402_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_processing_jobs",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_document_processing_jobs_case_id_cases")),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_document_processing_jobs_document_id_documents"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_processing_jobs")),
        sa.UniqueConstraint(
            "document_id",
            "job_type",
            "version_number",
            name="uq_document_processing_jobs_doc_job_version",
        ),
    )
    op.create_index(op.f("ix_document_processing_jobs_case_id"), "document_processing_jobs", ["case_id"], unique=False)
    op.create_index(op.f("ix_document_processing_jobs_document_id"), "document_processing_jobs", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_processing_jobs_job_type"), "document_processing_jobs", ["job_type"], unique=False)
    op.create_index(op.f("ix_document_processing_jobs_status"), "document_processing_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_processing_jobs_status"), table_name="document_processing_jobs")
    op.drop_index(op.f("ix_document_processing_jobs_job_type"), table_name="document_processing_jobs")
    op.drop_index(op.f("ix_document_processing_jobs_document_id"), table_name="document_processing_jobs")
    op.drop_index(op.f("ix_document_processing_jobs_case_id"), table_name="document_processing_jobs")
    op.drop_table("document_processing_jobs")
