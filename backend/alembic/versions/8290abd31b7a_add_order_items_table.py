"""add order items table

Revision ID: 8290abd31b7a
Revises: 258d978629fe
Create Date: 2026-10-31 16:40:12.596275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8290abd31b7a'
down_revision: Union[str, Sequence[str], None] = '258d978629fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass