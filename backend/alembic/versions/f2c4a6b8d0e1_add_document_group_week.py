"""add group, week and material type to documents

Materialet e lëndëve (ligjërata dhe ushtrime javore) i përkasin një
grupi, pra një profesori, dhe një jave të semestrit.

Revision ID: f2c4a6b8d0e1
Revises: e7b3d9a1c5f2
Create Date: 2026-09-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2c4a6b8d0e1'
down_revision: Union[str, Sequence[str], None] = 'e7b3d9a1c5f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('documents', sa.Column('group_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_documents_group_id', 'documents', 'course_groups',
        ['group_id'], ['id'], ondelete='SET NULL',
    )
    op.create_index('ix_documents_group_id', 'documents', ['group_id'])
    op.add_column('documents', sa.Column('week', sa.Integer(), nullable=True))
    op.add_column(
        'documents', sa.Column('material_type', sa.String(length=20), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('documents', 'material_type')
    op.drop_column('documents', 'week')
    op.drop_index('ix_documents_group_id', table_name='documents')
    op.drop_constraint('fk_documents_group_id', 'documents', type_='foreignkey')
    op.drop_column('documents', 'group_id')
