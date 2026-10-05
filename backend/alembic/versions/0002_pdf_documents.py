"""Store PDF metadata and extracted page text; preserve existing rows."""
from alembic import op
import sqlalchemy as sa

revision = "0002_pdf_documents"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("documents", sa.Column("size_bytes", sa.Integer(), server_default="0", nullable=False))
    op.add_column("documents", sa.Column("status", sa.String(20), server_default="uploaded", nullable=False))
    op.add_column("documents", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("error_message", sa.String(500), nullable=True))
    # Week 2/3 rows had filenames only, no physical PDF. Do not report success.
    op.execute(sa.text("UPDATE documents SET status='failed', error_message='Tài liệu cũ chưa có file PDF. Vui lòng tải lại.'"))
    op.create_check_constraint("ck_documents_status", "documents", "status IN ('uploaded', 'ready', 'failed')")
    op.create_table("document_pages",
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("page_number", sa.Integer(), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False))


def downgrade():
    op.drop_table("document_pages")
    op.drop_constraint("ck_documents_status", "documents", type_="check")
    for name in ("error_message", "page_count", "status", "size_bytes"):
        op.drop_column("documents", name)
