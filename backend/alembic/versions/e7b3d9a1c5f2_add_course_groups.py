"""add course groups for courses taught by several professors

Çdo lëndë me profesor merr një "Grupi A" me atë profesor, dhe
regjistrimet ekzistuese kalojnë në të, që asnjë student të mos mbetet
pa profesor pas migrimit.

Revision ID: e7b3d9a1c5f2
Revises: d5a1c2e3f4b6
Create Date: 2026-09-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7b3d9a1c5f2'
down_revision: Union[str, Sequence[str], None] = 'd5a1c2e3f4b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'course_groups',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'course_id',
            sa.Integer(),
            sa.ForeignKey('courses.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column(
            'professor_id',
            sa.Integer(),
            sa.ForeignKey('professors.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.UniqueConstraint('course_id', 'name', name='uq_course_groups_course_name'),
    )
    op.create_index('ix_course_groups_id', 'course_groups', ['id'])
    op.create_index('ix_course_groups_course_id', 'course_groups', ['course_id'])
    op.create_index('ix_course_groups_professor_id', 'course_groups', ['professor_id'])

    op.add_column('enrollments', sa.Column('group_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_enrollments_group_id', 'enrollments', 'course_groups',
        ['group_id'], ['id'], ondelete='SET NULL',
    )
    op.create_index('ix_enrollments_group_id', 'enrollments', ['group_id'])

    op.add_column('schedules', sa.Column('group_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_schedules_group_id', 'schedules', 'course_groups',
        ['group_id'], ['id'], ondelete='CASCADE',
    )
    op.create_index('ix_schedules_group_id', 'schedules', ['group_id'])

    op.execute(
        "INSERT INTO course_groups (course_id, name, professor_id) "
        "SELECT id, 'Grupi A', professor_id FROM courses "
        "WHERE professor_id IS NOT NULL"
    )
    op.execute(
        "UPDATE enrollments SET group_id = ("
        "  SELECT g.id FROM course_groups g "
        "  WHERE g.course_id = enrollments.course_id AND g.name = 'Grupi A'"
        ")"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_schedules_group_id', table_name='schedules')
    op.drop_constraint('fk_schedules_group_id', 'schedules', type_='foreignkey')
    op.drop_column('schedules', 'group_id')
    op.drop_index('ix_enrollments_group_id', table_name='enrollments')
    op.drop_constraint('fk_enrollments_group_id', 'enrollments', type_='foreignkey')
    op.drop_column('enrollments', 'group_id')
    op.drop_index('ix_course_groups_professor_id', table_name='course_groups')
    op.drop_index('ix_course_groups_course_id', table_name='course_groups')
    op.drop_index('ix_course_groups_id', table_name='course_groups')
    op.drop_table('course_groups')
