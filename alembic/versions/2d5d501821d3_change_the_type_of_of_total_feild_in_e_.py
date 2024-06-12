"""change the type of of total feild in e_commerce orders

Revision ID: 2d5d501821d3
Revises: 0e93316afb8b
Create Date: 2023-11-20 13:43:13.853338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2d5d501821d3'
down_revision: Union[str, None] = '0e93316afb8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #drop the total column in e_commerce_orders
    op.drop_column('e_commerce_orders', 'total')
    #create new total column with data type float
    op.add_column('e_commerce_orders', sa.Column('total', sa.Float(), nullable=False))
    pass

def downgrade() -> None:
    #drop the total column in e_commerce_orders
    op.drop_column('e_commerce_orders', 'total')
    #create new total column with data type float
    op.add_column('e_commerce_orders', sa.Column('total', sa.String(), nullable=False))
    pass