"""academic periods, enrollment period and profile study year

Ndan katër koncepte që deri tani ngatërroheshin: viti i studimit (1-3)
riemërtohet nga academic_year në study_year; viti akademik kalendarik dhe
periudha (dimërore/verore) ruhen te academic_periods; regjistrimi lidhet me
periudhën kur ndiqet lënda. Programi shënon nëse ECTS-të janë zyrtare.

Revision ID: a4e6c8b0d2f3
Revises: f2c4a6b8d0e1
Create Date: 2026-10-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4e6c8b0d2f3'
down_revision: Union[str, Sequence[str], None] = 'f2c4a6b8d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'student_profiles', 'academic_year', new_column_name='study_year',
    )

    op.create_table(
        'academic_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('academic_year', sa.String(length=9), nullable=False),
        sa.Column('term', sa.String(length=10), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('academic_year', 'term', name='uq_academic_period'),
    )
    op.create_index(
        op.f('ix_academic_periods_id'), 'academic_periods', ['id'], unique=False,
    )

    op.add_column('enrollments', sa.Column('period_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_enrollments_period_id', 'enrollments', 'academic_periods',
        ['period_id'], ['id'], ondelete='SET NULL',
    )
    op.create_index(
        op.f('ix_enrollments_period_id'), 'enrollments', ['period_id'], unique=False,
    )

    op.add_column(
        'programs',
        sa.Column(
            'ects_is_official', sa.Boolean(), nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('programs', 'ects_is_official')

    op.drop_index(op.f('ix_enrollments_period_id'), table_name='enrollments')
    op.drop_constraint('fk_enrollments_period_id', 'enrollments', type_='foreignkey')
    op.drop_column('enrollments', 'period_id')

    op.drop_index(op.f('ix_academic_periods_id'), table_name='academic_periods')
    op.drop_table('academic_periods')

    op.alter_column(
        'student_profiles', 'study_year', new_column_name='academic_year',
    )
