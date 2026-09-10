"""add document indexing status

Revision ID: b7e2f4a11c08
Revises: a4c1d7b90e52
Create Date: 2026-09-08 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e2f4a11c08'
down_revision: Union[str, Sequence[str], None] = 'a4c1d7b90e52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'documents',
        sa.Column(
            'status',
            sa.String(length=20),
            nullable=False,
            server_default='PENDING',
        ),
    )
    op.add_column(
        'documents',
        sa.Column('status_detail', sa.Text(), nullable=True),
    )
    op.add_column(
        'documents',
        sa.Column(
            'chunk_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        'documents',
        sa.Column('indexed_at', sa.DateTime(), nullable=True),
    )

    op.create_index(
        op.f('ix_documents_status'),
        'documents',
        ['status'],
        unique=False,
    )

    # Dokumentet që janë ingestuar para këtij migrimi njihen nga
    # chunks që kanë lënë pas; pa këtë ato do të dukeshin PENDING
    # edhe pse janë të kërkueshme.
    op.execute(
        """
        UPDATE documents
        SET status = 'INDEXED',
            chunk_count = counted.total,
            indexed_at = documents.uploaded_at
        FROM (
            SELECT document_id, COUNT(*) AS total
            FROM document_chunks
            GROUP BY document_id
        ) AS counted
        WHERE documents.id = counted.document_id
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_documents_status'), table_name='documents')

    op.drop_column('documents', 'indexed_at')
    op.drop_column('documents', 'chunk_count')
    op.drop_column('documents', 'status_detail')
    op.drop_column('documents', 'status')
