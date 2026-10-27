"""Quiz snapshots and one immutable scored attempt per quiz."""
from alembic import op
import sqlalchemy as sa
revision = '0006_quizzes'
down_revision = '0005_study_plans'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('quizzes',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('conversation_id', sa.Uuid(), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('spec', sa.JSON(), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'approved')", name='ck_quiz_status'))
    op.create_index('ix_quizzes_workspace_id', 'quizzes', ['workspace_id'])
    op.create_index('ix_quizzes_conversation_id', 'quizzes', ['conversation_id'])
    op.create_table('quiz_attempts',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('quiz_id', sa.Uuid(), sa.ForeignKey('quizzes.id'), nullable=False, unique=True),
        sa.Column('answers', sa.JSON(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False))


def downgrade():
    op.drop_table('quiz_attempts')
    op.drop_table('quizzes')
