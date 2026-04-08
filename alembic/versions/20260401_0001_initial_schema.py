from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260401_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("actor_reference", sa.String(length=255), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)

    op.create_table(
        "clients",
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clients")),
        sa.UniqueConstraint("email", name=op.f("uq_clients_email")),
    )
    op.create_index(op.f("ix_clients_email"), "clients", ["email"], unique=False)

    op.create_table(
        "cases",
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_number", sa.String(length=100), nullable=False),
        sa.Column("case_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], name=op.f("fk_cases_client_id_clients")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cases")),
        sa.UniqueConstraint("case_number", name=op.f("uq_cases_case_number")),
    )
    op.create_index(op.f("ix_cases_case_number"), "cases", ["case_number"], unique=False)
    op.create_index(op.f("ix_cases_case_type"), "cases", ["case_type"], unique=False)
    op.create_index(op.f("ix_cases_client_id"), "cases", ["client_id"], unique=False)
    op.create_index(op.f("ix_cases_status"), "cases", ["status"], unique=False)

    op.create_table(
        "documents",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("processing_status", sa.String(length=50), nullable=False),
        sa.Column("extracted_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_documents_case_id_cases")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_documents_storage_key")),
    )
    op.create_index(op.f("ix_documents_case_id"), "documents", ["case_id"], unique=False)
    op.create_index(op.f("ix_documents_document_type"), "documents", ["document_type"], unique=False)
    op.create_index(op.f("ix_documents_processing_status"), "documents", ["processing_status"], unique=False)

    op.create_table(
        "inconsistencies",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(length=150), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_inconsistencies_case_id_cases")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_inconsistencies")),
    )
    op.create_index(op.f("ix_inconsistencies_case_id"), "inconsistencies", ["case_id"], unique=False)
    op.create_index(op.f("ix_inconsistencies_field_name"), "inconsistencies", ["field_name"], unique=False)
    op.create_index(op.f("ix_inconsistencies_severity"), "inconsistencies", ["severity"], unique=False)
    op.create_index(op.f("ix_inconsistencies_status"), "inconsistencies", ["status"], unique=False)

    op.create_table(
        "participants",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_participants_case_id_cases")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_participants")),
    )
    op.create_index(op.f("ix_participants_case_id"), "participants", ["case_id"], unique=False)

    op.create_table(
        "questionnaires",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_questionnaires_case_id_cases")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questionnaires")),
    )
    op.create_index(op.f("ix_questionnaires_case_id"), "questionnaires", ["case_id"], unique=False)
    op.create_index(op.f("ix_questionnaires_status"), "questionnaires", ["status"], unique=False)

    op.create_table(
        "reviews",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_reference", sa.String(length=255), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_reviews_case_id_cases")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reviews")),
    )
    op.create_index(op.f("ix_reviews_case_id"), "reviews", ["case_id"], unique=False)
    op.create_index(op.f("ix_reviews_decision"), "reviews", ["decision"], unique=False)

    op.create_table(
        "case_canonical_fields",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("field_name", sa.String(length=150), nullable=False),
        sa.Column("field_value_text", sa.Text(), nullable=True),
        sa.Column("field_value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence_score", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_case_canonical_fields_case_id_cases")),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["documents.id"],
            name=op.f("fk_case_canonical_fields_source_document_id_documents"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_canonical_fields")),
    )
    op.create_index(op.f("ix_case_canonical_fields_case_id"), "case_canonical_fields", ["case_id"], unique=False)
    op.create_index(
        op.f("ix_case_canonical_fields_field_name"),
        "case_canonical_fields",
        ["field_name"],
        unique=False,
    )

    op.create_table(
        "questionnaire_responses",
        sa.Column("questionnaire_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_key", sa.String(length=100), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("answer_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["questionnaire_id"],
            ["questionnaires.id"],
            name=op.f("fk_questionnaire_responses_questionnaire_id_questionnaires"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questionnaire_responses")),
    )
    op.create_index(
        op.f("ix_questionnaire_responses_question_key"),
        "questionnaire_responses",
        ["question_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_questionnaire_responses_questionnaire_id"),
        "questionnaire_responses",
        ["questionnaire_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_questionnaire_responses_questionnaire_id"), table_name="questionnaire_responses")
    op.drop_index(op.f("ix_questionnaire_responses_question_key"), table_name="questionnaire_responses")
    op.drop_table("questionnaire_responses")
    op.drop_index(op.f("ix_case_canonical_fields_field_name"), table_name="case_canonical_fields")
    op.drop_index(op.f("ix_case_canonical_fields_case_id"), table_name="case_canonical_fields")
    op.drop_table("case_canonical_fields")
    op.drop_index(op.f("ix_reviews_decision"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_case_id"), table_name="reviews")
    op.drop_table("reviews")
    op.drop_index(op.f("ix_questionnaires_status"), table_name="questionnaires")
    op.drop_index(op.f("ix_questionnaires_case_id"), table_name="questionnaires")
    op.drop_table("questionnaires")
    op.drop_index(op.f("ix_participants_case_id"), table_name="participants")
    op.drop_table("participants")
    op.drop_index(op.f("ix_inconsistencies_status"), table_name="inconsistencies")
    op.drop_index(op.f("ix_inconsistencies_severity"), table_name="inconsistencies")
    op.drop_index(op.f("ix_inconsistencies_field_name"), table_name="inconsistencies")
    op.drop_index(op.f("ix_inconsistencies_case_id"), table_name="inconsistencies")
    op.drop_table("inconsistencies")
    op.drop_index(op.f("ix_documents_processing_status"), table_name="documents")
    op.drop_index(op.f("ix_documents_document_type"), table_name="documents")
    op.drop_index(op.f("ix_documents_case_id"), table_name="documents")
    op.drop_table("documents")
    op.drop_index(op.f("ix_cases_status"), table_name="cases")
    op.drop_index(op.f("ix_cases_client_id"), table_name="cases")
    op.drop_index(op.f("ix_cases_case_type"), table_name="cases")
    op.drop_index(op.f("ix_cases_case_number"), table_name="cases")
    op.drop_table("cases")
    op.drop_index(op.f("ix_clients_email"), table_name="clients")
    op.drop_table("clients")
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")
