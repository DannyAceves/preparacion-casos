from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260402_0003"
down_revision = "20260401_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("uploaded_by_user_id", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("stored_filename", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("storage_backend", sa.String(length=50), nullable=True))
    op.alter_column("documents", "storage_key", type_=sa.String(length=500), existing_type=sa.String(length=255))
    op.add_column("documents", sa.Column("sha256_hash", sa.String(length=64), nullable=True))
    op.add_column("documents", sa.Column("document_status", sa.String(length=50), nullable=True))
    op.add_column("documents", sa.Column("classification_label", sa.String(length=100), nullable=True))
    op.add_column("documents", sa.Column("classification_source", sa.String(length=50), nullable=True))
    op.add_column("documents", sa.Column("file_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("documents", sa.Column("version_number", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("is_current", sa.Boolean(), nullable=True))
    op.add_column("documents", sa.Column("previous_version_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("documents", sa.Column("root_document_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("documents", sa.Column("replacement_notes", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True))

    op.create_foreign_key(
        op.f("fk_documents_previous_version_id_documents"),
        "documents",
        "documents",
        ["previous_version_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_documents_root_document_id_documents"),
        "documents",
        "documents",
        ["root_document_id"],
        ["id"],
    )

    op.execute("UPDATE documents SET uploaded_by_user_id = 'system-seed' WHERE uploaded_by_user_id IS NULL")
    op.execute("UPDATE documents SET stored_filename = original_filename WHERE stored_filename IS NULL")
    op.execute("UPDATE documents SET storage_backend = 'local' WHERE storage_backend IS NULL")
    op.execute("UPDATE documents SET sha256_hash = repeat('0', 64) WHERE sha256_hash IS NULL")
    op.execute("UPDATE documents SET document_status = processing_status WHERE document_status IS NULL")
    op.execute("UPDATE documents SET classification_label = document_type WHERE classification_label IS NULL")
    op.execute(
        "UPDATE documents SET classification_source = 'legacy' WHERE classification_label IS NOT NULL "
        "AND classification_source IS NULL"
    )
    op.execute("UPDATE documents SET file_metadata = jsonb_build_object('size_bytes', size_bytes) WHERE file_metadata IS NULL")
    op.execute("UPDATE documents SET version_number = 1 WHERE version_number IS NULL")
    op.execute("UPDATE documents SET is_current = true WHERE is_current IS NULL")
    op.execute("UPDATE documents SET uploaded_at = created_at WHERE uploaded_at IS NULL")
    op.execute("UPDATE documents SET root_document_id = id WHERE root_document_id IS NULL")

    op.alter_column("documents", "uploaded_by_user_id", nullable=False)
    op.alter_column("documents", "stored_filename", nullable=False)
    op.alter_column("documents", "storage_backend", nullable=False)
    op.alter_column("documents", "sha256_hash", nullable=False)
    op.alter_column("documents", "document_status", nullable=False)
    op.alter_column("documents", "version_number", nullable=False)
    op.alter_column("documents", "is_current", nullable=False)
    op.alter_column("documents", "uploaded_at", nullable=False)
    op.create_index(op.f("ix_documents_uploaded_by_user_id"), "documents", ["uploaded_by_user_id"], unique=False)
    op.create_index(op.f("ix_documents_sha256_hash"), "documents", ["sha256_hash"], unique=False)
    op.create_index(op.f("ix_documents_document_status"), "documents", ["document_status"], unique=False)
    op.create_index(op.f("ix_documents_classification_label"), "documents", ["classification_label"], unique=False)
    op.create_index(op.f("ix_documents_is_current"), "documents", ["is_current"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_is_current"), table_name="documents")
    op.drop_index(op.f("ix_documents_classification_label"), table_name="documents")
    op.drop_index(op.f("ix_documents_document_status"), table_name="documents")
    op.drop_index(op.f("ix_documents_sha256_hash"), table_name="documents")
    op.drop_index(op.f("ix_documents_uploaded_by_user_id"), table_name="documents")
    op.drop_constraint(op.f("fk_documents_root_document_id_documents"), "documents", type_="foreignkey")
    op.drop_constraint(op.f("fk_documents_previous_version_id_documents"), "documents", type_="foreignkey")
    op.drop_column("documents", "uploaded_at")
    op.drop_column("documents", "replacement_notes")
    op.drop_column("documents", "root_document_id")
    op.drop_column("documents", "previous_version_id")
    op.drop_column("documents", "is_current")
    op.drop_column("documents", "version_number")
    op.drop_column("documents", "file_metadata")
    op.drop_column("documents", "classification_source")
    op.drop_column("documents", "classification_label")
    op.drop_column("documents", "document_status")
    op.drop_column("documents", "sha256_hash")
    op.alter_column("documents", "storage_key", type_=sa.String(length=255), existing_type=sa.String(length=500))
    op.drop_column("documents", "storage_backend")
    op.drop_column("documents", "stored_filename")
    op.drop_column("documents", "uploaded_by_user_id")
