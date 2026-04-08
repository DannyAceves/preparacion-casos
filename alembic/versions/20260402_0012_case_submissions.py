from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260402_0012"
down_revision = "20260402_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("approved_for_submission_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("submission_reference", sa.String(length=255), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_case_submissions_case_id_cases")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_submissions")),
        sa.UniqueConstraint("case_id", name="uq_case_submissions_case_id"),
    )
    op.create_index(op.f("ix_case_submissions_case_id"), "case_submissions", ["case_id"], unique=False)
    op.create_index(op.f("ix_case_submissions_status"), "case_submissions", ["status"], unique=False)
    op.create_index(op.f("ix_case_submissions_submission_reference"), "case_submissions", ["submission_reference"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_case_submissions_submission_reference"), table_name="case_submissions")
    op.drop_index(op.f("ix_case_submissions_status"), table_name="case_submissions")
    op.drop_index(op.f("ix_case_submissions_case_id"), table_name="case_submissions")
    op.drop_table("case_submissions")
