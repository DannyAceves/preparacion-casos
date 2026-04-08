from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260404_0013"
down_revision = "20260402_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consultations",
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("appointment_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_attorney", sa.String(length=255), nullable=True),
        sa.Column("reception_notes", sa.Text(), nullable=True),
        sa.Column("intake_answers", sa.Text(), nullable=True),
        sa.Column("suggested_case_type", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("converted_case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], name=op.f("fk_consultations_client_id_clients")),
        sa.ForeignKeyConstraint(
            ["converted_case_id"],
            ["cases.id"],
            name=op.f("fk_consultations_converted_case_id_cases"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_consultations")),
        sa.UniqueConstraint("converted_case_id", name=op.f("uq_consultations_converted_case_id")),
    )
    op.create_index(op.f("ix_consultations_client_id"), "consultations", ["client_id"], unique=False)
    op.create_index(op.f("ix_consultations_converted_case_id"), "consultations", ["converted_case_id"], unique=False)
    op.create_index(op.f("ix_consultations_email"), "consultations", ["email"], unique=False)
    op.create_index(op.f("ix_consultations_status"), "consultations", ["status"], unique=False)
    op.create_index(op.f("ix_consultations_suggested_case_type"), "consultations", ["suggested_case_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_consultations_suggested_case_type"), table_name="consultations")
    op.drop_index(op.f("ix_consultations_status"), table_name="consultations")
    op.drop_index(op.f("ix_consultations_email"), table_name="consultations")
    op.drop_index(op.f("ix_consultations_converted_case_id"), table_name="consultations")
    op.drop_index(op.f("ix_consultations_client_id"), table_name="consultations")
    op.drop_table("consultations")
