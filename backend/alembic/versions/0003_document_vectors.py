"""Add independent indexing state and page-aware pgvector chunks."""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0003_document_vectors"
down_revision = "0002_pdf_documents"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public")
    for column in (
        sa.Column("index_status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("index_error", sa.String(500)),
        sa.Column("index_job_id", sa.Uuid()),
        sa.Column("index_started_at", sa.DateTime(timezone=True)),
        sa.Column("indexed_at", sa.DateTime(timezone=True)),
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("embedding_model", sa.String(200)),
    ):
        op.add_column("documents", column)
    op.create_check_constraint("ck_documents_index_status", "documents", "index_status IN ('pending', 'processing', 'ready', 'failed')")
    op.create_table("document_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1024), nullable=False),
        sa.Column("embedding_model", sa.String(200), nullable=False),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"))
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])


def downgrade():
    op.drop_table("document_chunks")
    op.drop_constraint("ck_documents_index_status", "documents", type_="check")
    for name in ("embedding_model", "chunk_count", "indexed_at", "index_started_at", "index_job_id", "index_error", "index_status"):
        op.drop_column("documents", name)
    # Extension may be shared by other schemas; never drop it here.
