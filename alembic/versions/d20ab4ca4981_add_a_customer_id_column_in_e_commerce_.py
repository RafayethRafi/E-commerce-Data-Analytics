"""add a customer_id column in e_commerce_orders table

Revision ID: d20ab4ca4981
Revises: 9996108ee4af
Create Date: 2023-12-03 16:43:37.940730

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd20ab4ca4981'
down_revision: Union[str, None] = '9996108ee4af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #server_default is 0 in int
    op.add_column('e_commerce_orders', sa.Column('customer_id', sa.BigInteger(), nullable=True, server_default="0"))
    pass

def downgrade() -> None:
    op.drop_column('e_commerce_orders', 'customer_id')
    pass