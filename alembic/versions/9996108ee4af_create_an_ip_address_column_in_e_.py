"""create an ip_address column in e_commerce_orders table

Revision ID: 9996108ee4af
Revises: 2d5d501821d3
Create Date: 2023-12-02 19:55:34.210918

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9996108ee4af'
down_revision: Union[str, None] = '2d5d501821d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('e_commerce_orders', sa.Column('ip_address', sa.String(), nullable=True, server_default=''))
    pass


def downgrade() -> None:
    op.drop_column('e_commerce_orders', 'ip_address')
    pass