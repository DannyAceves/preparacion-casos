from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260402_0005"
down_revision = "20260402_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("inconsistencies", sa.Column("field_key", sa.String(length=150), nullable=True))
    op.add_column("inconsistencies", sa.Column("resolution_notes", sa.Text(), nullable=True))
    op.add_column("inconsistencies", sa.Column("resolved_by_user_id", sa.String(length=255), nullable=True))
    op.add_column("inconsistencies", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE inconsistencies SET field_key = field_name WHERE field_key IS NULL")
    op.alter_column("inconsistencies", "field_key", nullable=False)

    op.drop_index(op.f("ix_inconsistencies_field_name"), table_name="inconsistencies")
    op.drop_column("inconsistencies", "field_name")
    op.create_index(op.f("ix_inconsistencies_field_key"), "inconsistencies", ["field_key"], unique=False)


def downgrade() -> None:
    op.add_column("inconsistencies", sa.Column("field_name", sa.String(length=150), nullable=True))
    op.execute("UPDATE inconsistencies SET field_name = field_key WHERE field_name IS NULL")
    op.alter_column("inconsistencies", "field_name", nullable=False)
    op.drop_index(op.f("ix_inconsistencies_field_key"), table_name="inconsistencies")
    op.drop_column("inconsistencies", "resolved_at")
    op.drop_column("inconsistencies", "resolved_by_user_id")
    op.drop_column("inconsistencies", "resolution_notes")
    op.drop_column("inconsistencies", "field_key")
    op.create_index(op.f("ix_inconsistencies_field_name"), "inconsistencies", ["field_name"], unique=False)
