"""normalize document file paths to forward slashes

Dokumentet e ngarkuara ose të seed-uara kur API-ja ekzekutohej në
Windows u ruajtën me "\\" (uploads\\documents\\x.pdf). Brenda Docker-it
(Linux) ai shteg nuk hapet, prandaj ri-indeksimi dështonte.

Revision ID: c3d8e1f20a47
Revises: b7e2f4a11c08
Create Date: 2026-09-28 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c3d8e1f20a47'
down_revision: Union[str, Sequence[str], None] = 'b7e2f4a11c08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Pa WHERE: te LIKE "\" është karakter escape-i, dhe REPLACE mbi
    # një shteg pa "\" nuk ndryshon asgjë.
    op.execute(
        "UPDATE documents SET file_path = REPLACE(file_path, '\\', '/')"
    )


def downgrade() -> None:
    """Downgrade schema.

    Nuk ka kthim: shtegu me "/" hapet në çdo sistem, ndërsa ai me "\\"
    vetëm në Windows.
    """
