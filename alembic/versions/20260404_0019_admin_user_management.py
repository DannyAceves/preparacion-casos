"""admin user management

Revision ID: 20260404_0019
Revises: 20260404_0018
Create Date: 2026-04-04 17:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260404_0019"
down_revision = "20260404_0018"
branch_labels = None
depends_on = None


system_role_enum = postgresql.ENUM(
    "admin",
    "reception",
    "attorney",
    "paralegal",
    "client",
    name="system_role_enum",
    create_type=False,
)


def upgrade() -> None:
    system_role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "system_users",
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", system_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_system_users")),
        sa.UniqueConstraint("email", name=op.f("uq_system_users_email")),
    )
    op.create_index(op.f("ix_system_users_email"), "system_users", ["email"], unique=False)
    op.create_index(op.f("ix_system_users_role"), "system_users", ["role"], unique=False)
    op.create_index(op.f("ix_system_users_is_active"), "system_users", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_system_users_is_active"), table_name="system_users")
    op.drop_index(op.f("ix_system_users_role"), table_name="system_users")
    op.drop_index(op.f("ix_system_users_email"), table_name="system_users")
    op.drop_table("system_users")
    system_role_enum.drop(op.get_bind(), checkfirst=True)
