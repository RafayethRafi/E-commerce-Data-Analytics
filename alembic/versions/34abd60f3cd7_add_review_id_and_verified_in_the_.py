"""add review_id and verified in the reviews table

Revision ID: 34abd60f3cd7
Revises: b970661e5bc7
Create Date: 2023-10-26 20:02:40.855394

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '34abd60f3cd7'
down_revision: Union[str, None] = 'b970661e5bc7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('woocommerce_reviews', sa.Column('review_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('woocommerce_reviews', sa.Column('verified', sa.BOOLEAN(), autoincrement=False, nullable=False,default=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('woocommerce_reviews', 'verified')
    op.drop_column('woocommerce_reviews', 'review_id')
    # ### end Alembic commands ###
