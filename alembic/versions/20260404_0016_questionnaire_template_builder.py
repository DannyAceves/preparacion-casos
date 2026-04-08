from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260404_0016"
down_revision = "20260404_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questionnaire_questions",
        sa.Column("conditional_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "questionnaire_questions",
        sa.Column("field_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.drop_constraint(op.f("uq_questionnaire_questions_key"), "questionnaire_questions", type_="unique")

    op.add_column(
        "questionnaires",
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "questionnaires",
        sa.Column("template_version", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_questionnaires_template_id_questionnaire_templates"),
        "questionnaires",
        "questionnaire_templates",
        ["template_id"],
        ["id"],
    )
    op.create_index(op.f("ix_questionnaires_template_id"), "questionnaires", ["template_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_questionnaires_template_id"), table_name="questionnaires")
    op.drop_constraint(op.f("fk_questionnaires_template_id_questionnaire_templates"), "questionnaires", type_="foreignkey")
    op.drop_column("questionnaires", "template_version")
    op.drop_column("questionnaires", "template_id")

    op.create_unique_constraint(op.f("uq_questionnaire_questions_key"), "questionnaire_questions", ["key"])
    op.drop_column("questionnaire_questions", "field_config")
    op.drop_column("questionnaire_questions", "conditional_rules")
