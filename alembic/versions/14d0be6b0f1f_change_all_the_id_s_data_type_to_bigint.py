"""change all the id's data type to bigint

Revision ID: 14d0be6b0f1f
Revises: 4f78b67863d1
Create Date: 2023-11-18 22:24:04.584570

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '14d0be6b0f1f'
down_revision: Union[str, None] = '4f78b67863d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #change all the id columns to bigint
    op.alter_column('e_commerce_reviews', 'product_id', type_=sa.BigInteger())
    op.alter_column('e_commerce_reviews', 'review_id', type_=sa.BigInteger())

    op.alter_column('e_commerce_orders', 'order_id', type_=sa.BigInteger())



def downgrade() -> None:

    op.alter_column('e_commerce_reviews', 'product_id', type_=sa.Integer())
    op.alter_column('e_commerce_reviews', 'review_id', type_=sa.Integer())

    op.alter_column('e_commerce_orders', 'order_id', type_=sa.Integer())

