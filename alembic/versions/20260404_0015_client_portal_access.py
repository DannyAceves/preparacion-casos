from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260404_0015"
down_revision = "20260404_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_portal_accesses",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("token_last4", sa.String(length=4), nullable=False),
        sa.Column("passcode_hash", sa.String(length=64), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_client_portal_accesses_case_id_cases")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_portal_accesses")),
        sa.UniqueConstraint("case_id", name=op.f("uq_client_portal_accesses_case_id")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_client_portal_accesses_token_hash")),
    )
    op.create_index(op.f("ix_client_portal_accesses_case_id"), "client_portal_accesses", ["case_id"], unique=False)
    op.create_index(op.f("ix_client_portal_accesses_is_active"), "client_portal_accesses", ["is_active"], unique=False)
    op.create_index(op.f("ix_client_portal_accesses_token_hash"), "client_portal_accesses", ["token_hash"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_client_portal_accesses_token_hash"), table_name="client_portal_accesses")
    op.drop_index(op.f("ix_client_portal_accesses_is_active"), table_name="client_portal_accesses")
    op.drop_index(op.f("ix_client_portal_accesses_case_id"), table_name="client_portal_accesses")
    op.drop_table("client_portal_accesses")
