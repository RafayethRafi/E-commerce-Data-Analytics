"""update the order_id feild in rcommerce_orders table from int to string

Revision ID: 1de09f4d773a
Revises: 14d0be6b0f1f
Create Date: 2023-11-19 23:02:17.033040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1de09f4d773a'
down_revision: Union[str, None] = '14d0be6b0f1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('e_commerce_orders', 'order_id', type_=sa.String())
    op.alter_column('e_commerce_orders', 'line_items', type_=postgresql.ARRAY(sa.String()))


def downgrade() -> None:
    op.alter_column('e_commerce_orders', 'order_id', type_=sa.Integer())
    op.alter_column('e_commerce_orders', 'line_items', type_=postgresql.ARRAY(sa.Integer()))