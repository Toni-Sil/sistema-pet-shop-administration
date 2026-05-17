"""Add agent system tables

Revision ID: add_agent_system
Revises: 6e985e4700a8
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_agent_system'
down_revision = '6e985e4700a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'agent_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('role', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('max_tokens', sa.Integer, default=512),
        sa.Column('temperature', sa.Float, default=0.2),
        sa.Column('permissions', sa.JSON, default=list),
        sa.Column('tools', sa.JSON, default=list),
        sa.Column('triggers', sa.JSON, default=list),
        sa.Column('workflow', sa.JSON, default=list),
        sa.Column('escalation_rules', sa.JSON, default=list),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('priority', sa.Integer, default=5),
        sa.Column('parent_agent', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_agent_definitions_store_id', 'agent_definitions', ['store_id'])

    op.create_table(
        'agent_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('state', sa.String(50), default='idle'),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('input_data', sa.JSON, default=dict),
        sa.Column('output_data', sa.JSON, default=dict),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('execution_mode', sa.String(50), default='async'),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('correlation_id', sa.String(100), nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=True),
    )
    op.create_index('ix_agent_executions_agent_id', 'agent_executions', ['agent_id'])
    op.create_index('ix_agent_executions_store_id', 'agent_executions', ['store_id'])
    op.create_index('ix_agent_executions_correlation_id', 'agent_executions', ['correlation_id'])

    op.create_table(
        'agent_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('memory_type', sa.String(50), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.Text, nullable=True),
        sa.Column('tags', sa.JSON, default=list),
        sa.Column('importance', sa.Integer, default=5),
        sa.Column('embedding', sa.JSON, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('metadata', sa.JSON, default=dict),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_agent_memories_agent_id', 'agent_memories', ['agent_id'])
    op.create_index('ix_agent_memories_store_id', 'agent_memories', ['store_id'])

    op.create_table(
        'agent_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('source_agent', sa.String(100), nullable=True),
        sa.Column('target_agent', sa.String(100), nullable=True),
        sa.Column('payload', sa.JSON, default=dict),
        sa.Column('metadata', sa.JSON, default=dict),
        sa.Column('correlation_id', sa.String(100), nullable=True),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_agent_events_store_id', 'agent_events', ['store_id'])
    op.create_index('ix_agent_events_event_type', 'agent_events', ['event_type'])
    op.create_index('ix_agent_events_correlation_id', 'agent_events', ['correlation_id'])
    op.create_index('ix_agent_events_timestamp', 'agent_events', ['timestamp'])

    op.create_table(
        'escalation_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('from_agent', sa.String(100), nullable=False),
        sa.Column('to_agent', sa.String(100), nullable=False),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
        sa.Column('resolution', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_escalation_logs_store_id', 'escalation_logs', ['store_id'])

    op.create_table(
        'approval_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('details', sa.JSON, default=dict),
        sa.Column('requester', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('approver', sa.String(100), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('rejected_at', sa.DateTime, nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_approval_requests_store_id', 'approval_requests', ['store_id'])


def downgrade() -> None:
    op.drop_table('approval_requests')
    op.drop_table('escalation_logs')
    op.drop_table('agent_events')
    op.drop_table('agent_memories')
    op.drop_table('agent_executions')
    op.drop_table('agent_definitions')