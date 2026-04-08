from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260401_0002"
down_revision = "20260401_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "questionnaire_templates",
        sa.Column("case_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questionnaire_templates")),
    )
    op.create_index(op.f("ix_questionnaire_templates_case_type"), "questionnaire_templates", ["case_type"], unique=False)
    op.create_index(op.f("ix_questionnaire_templates_status"), "questionnaire_templates", ["status"], unique=False)

    op.create_table(
        "questionnaire_sections",
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["questionnaire_templates.id"],
            name=op.f("fk_questionnaire_sections_template_id_questionnaire_templates"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questionnaire_sections")),
    )
    op.create_index(op.f("ix_questionnaire_sections_template_id"), "questionnaire_sections", ["template_id"], unique=False)

    op.create_table(
        "questionnaire_questions",
        sa.Column("section_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("help_text", sa.Text(), nullable=True),
        sa.Column("input_type", sa.String(length=50), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("validation_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["questionnaire_sections.id"],
            name=op.f("fk_questionnaire_questions_section_id_questionnaire_sections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questionnaire_questions")),
        sa.UniqueConstraint("key", name=op.f("uq_questionnaire_questions_key")),
    )
    op.create_index(op.f("ix_questionnaire_questions_input_type"), "questionnaire_questions", ["input_type"], unique=False)
    op.create_index(op.f("ix_questionnaire_questions_key"), "questionnaire_questions", ["key"], unique=False)
    op.create_index(op.f("ix_questionnaire_questions_section_id"), "questionnaire_questions", ["section_id"], unique=False)

    op.create_table(
        "questionnaire_answers",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("answer_date", sa.Date(), nullable=True),
        sa.Column("answer_boolean", sa.Boolean(), nullable=True),
        sa.Column("answer_choice", sa.String(length=255), nullable=True),
        sa.Column("answer_choices", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("answer_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_questionnaire_answers_case_id_cases")),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questionnaire_questions.id"],
            name=op.f("fk_questionnaire_answers_question_id_questionnaire_questions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questionnaire_answers")),
        sa.UniqueConstraint(
            "case_id",
            "question_id",
            name="uq_questionnaire_answers_case_id_question_id",
        ),
    )
    op.create_index(op.f("ix_questionnaire_answers_case_id"), "questionnaire_answers", ["case_id"], unique=False)
    op.create_index(op.f("ix_questionnaire_answers_question_id"), "questionnaire_answers", ["question_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_questionnaire_answers_question_id"), table_name="questionnaire_answers")
    op.drop_index(op.f("ix_questionnaire_answers_case_id"), table_name="questionnaire_answers")
    op.drop_table("questionnaire_answers")
    op.drop_index(op.f("ix_questionnaire_questions_section_id"), table_name="questionnaire_questions")
    op.drop_index(op.f("ix_questionnaire_questions_key"), table_name="questionnaire_questions")
    op.drop_index(op.f("ix_questionnaire_questions_input_type"), table_name="questionnaire_questions")
    op.drop_table("questionnaire_questions")
    op.drop_index(op.f("ix_questionnaire_sections_template_id"), table_name="questionnaire_sections")
    op.drop_table("questionnaire_sections")
    op.drop_index(op.f("ix_questionnaire_templates_status"), table_name="questionnaire_templates")
    op.drop_index(op.f("ix_questionnaire_templates_case_type"), table_name="questionnaire_templates")
    op.drop_table("questionnaire_templates")
