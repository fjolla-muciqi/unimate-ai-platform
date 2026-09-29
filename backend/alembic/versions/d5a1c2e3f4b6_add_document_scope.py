"""add faculty and course scope to documents

Revision ID: d5a1c2e3f4b6
Revises: c3d8e1f20a47
Create Date: 2026-09-29 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5a1c2e3f4b6'
down_revision: Union[str, Sequence[str], None] = 'c3d8e1f20a47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'documents',
        sa.Column('faculty_id', sa.Integer(), nullable=True),
    )
    op.add_column(
        'documents',
        sa.Column('course_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_documents_faculty_id',
        'documents',
        'faculties',
        ['faculty_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_documents_course_id',
        'documents',
        'courses',
        ['course_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_documents_faculty_id', 'documents', ['faculty_id'])
    op.create_index('ix_documents_course_id', 'documents', ['course_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_documents_course_id', table_name='documents')
    op.drop_index('ix_documents_faculty_id', table_name='documents')
    op.drop_constraint('fk_documents_course_id', 'documents', type_='foreignkey')
    op.drop_constraint('fk_documents_faculty_id', 'documents', type_='foreignkey')
    op.drop_column('documents', 'course_id')
    op.drop_column('documents', 'faculty_id')
