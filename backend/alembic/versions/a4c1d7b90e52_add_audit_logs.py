"""add audit logs and message blocked_by

Revision ID: a4c1d7b90e52
Revises: 17f3093c12c7
Create Date: 2026-09-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4c1d7b90e52'
down_revision: Union[str, Sequence[str], None] = '17f3093c12c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('detail', sa.Text(), nullable=False),
        sa.Column('rule', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(
        op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False
    )
    op.create_index(
        op.f('ix_audit_logs_user_id'),
        'audit_logs',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_audit_logs_event_type'),
        'audit_logs',
        ['event_type'],
        unique=False,
    )
    op.create_index(
        op.f('ix_audit_logs_created_at'),
        'audit_logs',
        ['created_at'],
        unique=False,
    )

    op.add_column(
        'messages',
        sa.Column('blocked_by', sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('messages', 'blocked_by')

    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_event_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')

    op.drop_table('audit_logs')
