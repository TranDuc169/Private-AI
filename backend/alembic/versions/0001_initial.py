"""Initial ownership and workspace-scoped resource schema; no RAG tables yet."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def common_columns():
    return (
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def upgrade():
    op.create_table("users", *common_columns(),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False))
    op.create_table("workspaces", *common_columns(),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False))
    op.create_index("ix_workspaces_owner_id", "workspaces", ["owner_id"])
    op.create_table("documents", *common_columns(),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False))
    op.create_index("ix_documents_workspace_id", "documents", ["workspace_id"])
    op.create_table("conversations", *common_columns(),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False))
    op.create_index("ix_conversations_workspace_id", "conversations", ["workspace_id"])
    op.create_table("messages", *common_columns(),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_messages_role"))
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])


def downgrade():
    for table in ("messages", "conversations", "documents", "workspaces", "users"):
        op.drop_table(table)
