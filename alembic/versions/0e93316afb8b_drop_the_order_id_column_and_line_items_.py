"""drop the order_id column and line_items columns and create new order_id column and line_items column

Revision ID: 0e93316afb8b
Revises: 1de09f4d773a
Create Date: 2023-11-20 11:17:39.543699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0e93316afb8b'
down_revision: Union[str, None] = '1de09f4d773a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #deop order_id and line_items columns
    op.drop_column('e_commerce_orders', 'order_id')
    op.drop_column('e_commerce_orders', 'line_items')

    #create new order_id and line_items columns with data type bigint in both
    op.add_column('e_commerce_orders', sa.Column('order_id', sa.BigInteger(), nullable=False))
    #line items data type is array of big int
    op.add_column('e_commerce_orders', sa.Column('line_items', postgresql.ARRAY(sa.BigInteger()), nullable=False))
    pass
    


def downgrade() -> None:
    #drop the new order_id and line_items columns
    op.drop_column('e_commerce_orders', 'order_id')
    op.drop_column('e_commerce_orders', 'line_items')

    #create the old order_id and line_items columns
    op.add_column('e_commerce_orders', sa.Column('order_id', sa.Integer(), nullable=False))
    op.add_column('e_commerce_orders', sa.Column('line_items', postgresql.ARRAY(sa.Integer()), nullable=False))
    pass