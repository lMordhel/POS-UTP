"""snapshot codigo/nombre en movements (SPEC-STOCK-007)

Revision ID: c7d2e4f6a8b1
Revises: aec6516c0f10
Create Date: 2026-10-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d2e4f6a8b1'
down_revision: Union[str, None] = 'aec6516c0f10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('inventory_movements', sa.Column('codigo', sa.String(length=32), nullable=True))
    op.add_column('inventory_movements', sa.Column('nombre', sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column('inventory_movements', 'nombre')
    op.drop_column('inventory_movements', 'codigo')
