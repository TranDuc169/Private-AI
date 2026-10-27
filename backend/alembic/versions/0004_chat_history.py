"""Preserve existing messages; add ordered turns and source snapshots."""
from alembic import op
import sqlalchemy as sa

revision = '0004_chat_history'
down_revision = '0003_document_vectors'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('conversations', sa.Column('revision', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('messages', sa.Column('position', sa.Integer(), nullable=True))
    op.add_column('messages', sa.Column('payload', sa.JSON(), nullable=True))
    # Legacy messages retain content and are ordered before newly appended turns.


def downgrade():
    op.drop_column('messages', 'payload')
    op.drop_column('messages', 'position')
    op.drop_column('conversations', 'revision')
