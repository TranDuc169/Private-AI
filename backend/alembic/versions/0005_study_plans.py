"""Workspace study plans and persistent checklists."""
from alembic import op
import sqlalchemy as sa

revision = '0005_study_plans'
down_revision = '0004_chat_history'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('study_plans',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('conversation_id', sa.Uuid(), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('status', sa.String(20), server_default='draft', nullable=False),
        sa.Column('revision', sa.Integer(), server_default='0', nullable=False),
        sa.Column('spec', sa.JSON(), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'confirmed')", name='ck_study_plan_status'))
    op.create_index('ix_study_plans_workspace_id', 'study_plans', ['workspace_id'])
    op.create_index('ix_study_plans_conversation_id', 'study_plans', ['conversation_id'])
    op.create_table('study_steps',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('plan_id', sa.Uuid(), sa.ForeignKey('study_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_key', sa.String(40), nullable=False),
        sa.Column('done', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.UniqueConstraint('plan_id', 'step_key', name='uq_study_step_key'))
    op.create_index('ix_study_steps_plan_id', 'study_steps', ['plan_id'])


def downgrade():
    op.drop_table('study_steps')
    op.drop_table('study_plans')
