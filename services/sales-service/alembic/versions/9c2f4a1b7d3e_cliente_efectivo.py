"""sales cliente + efectivo (SPEC-SALES-005): solo add_column nullable.

Revision ID: 9c2f4a1b7d3e
Revises: 5df949f9a5f2
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c2f4a1b7d3e'
down_revision: Union[str, None] = '5df949f9a5f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sales', sa.Column('cliente', sa.String(length=120), nullable=True))
    op.add_column('sales', sa.Column('monto_recibido', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('sales', sa.Column('vuelto', sa.Numeric(precision=12, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column('sales', 'vuelto')
    op.drop_column('sales', 'monto_recibido')
    op.drop_column('sales', 'cliente')
