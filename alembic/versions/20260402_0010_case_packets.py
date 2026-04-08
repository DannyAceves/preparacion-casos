from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260402_0010"
down_revision = "20260402_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_packets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("packet_version", sa.Integer(), nullable=False),
        sa.Column("packet_status", sa.String(length=50), nullable=False),
        sa.Column("generated_by_reference", sa.String(length=255), nullable=True),
        sa.Column("summary_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("document_index", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("checklist_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("export_artifact", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("generation_notes", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_case_packets_case_id_cases")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_packets")),
    )
    op.create_index(op.f("ix_case_packets_case_id"), "case_packets", ["case_id"], unique=False)
    op.create_index(op.f("ix_case_packets_packet_status"), "case_packets", ["packet_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_case_packets_packet_status"), table_name="case_packets")
    op.drop_index(op.f("ix_case_packets_case_id"), table_name="case_packets")
    op.drop_table("case_packets")
