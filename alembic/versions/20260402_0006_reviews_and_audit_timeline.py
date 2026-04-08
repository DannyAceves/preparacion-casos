from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260402_0006"
down_revision = "20260402_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        op.f("fk_audit_logs_case_id_cases"),
        "audit_logs",
        "cases",
        ["case_id"],
        ["id"],
    )
    op.create_index(op.f("ix_audit_logs_case_id"), "audit_logs", ["case_id"], unique=False)

    op.execute(
        "UPDATE audit_logs SET case_id = NULLIF(payload->>'case_id', '')::uuid "
        "WHERE case_id IS NULL AND payload ? 'case_id'"
    )

    op.add_column("reviews", sa.Column("review_type", sa.String(length=50), nullable=True))
    op.execute("UPDATE reviews SET review_type = 'attorney' WHERE review_type IS NULL")
    op.execute("UPDATE reviews SET decision = 'fix_required' WHERE decision = 'pending'")
    op.alter_column("reviews", "review_type", nullable=False)
    op.create_index(op.f("ix_reviews_review_type"), "reviews", ["review_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reviews_review_type"), table_name="reviews")
    op.drop_column("reviews", "review_type")
    op.drop_index(op.f("ix_audit_logs_case_id"), table_name="audit_logs")
    op.drop_constraint(op.f("fk_audit_logs_case_id_cases"), "audit_logs", type_="foreignkey")
    op.drop_column("audit_logs", "case_id")
