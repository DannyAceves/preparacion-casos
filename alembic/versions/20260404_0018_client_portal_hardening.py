"""client portal hardening

Revision ID: 20260404_0018
Revises: 20260404_0017
Create Date: 2026-04-04 16:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260404_0018"
down_revision = "20260404_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("client_portal_accesses", sa.Column("access_session_hash", sa.String(length=64), nullable=True))
    op.add_column("client_portal_accesses", sa.Column("access_session_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "client_portal_accesses",
        sa.Column("failed_access_attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("client_portal_accesses", sa.Column("last_failed_access_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("client_portal_accesses", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        op.f("ix_client_portal_accesses_access_session_hash"),
        "client_portal_accesses",
        ["access_session_hash"],
        unique=True,
    )
    op.alter_column("client_portal_accesses", "failed_access_attempt_count", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_client_portal_accesses_access_session_hash"), table_name="client_portal_accesses")
    op.drop_column("client_portal_accesses", "locked_until")
    op.drop_column("client_portal_accesses", "last_failed_access_at")
    op.drop_column("client_portal_accesses", "failed_access_attempt_count")
    op.drop_column("client_portal_accesses", "access_session_expires_at")
    op.drop_column("client_portal_accesses", "access_session_hash")
