"""create woocommerce_clients table and woocommerce_reviews table

Revision ID: b7ed4c38d843
Revises: e20d2619bc78
Create Date: 2023-10-13 21:45:18.625660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7ed4c38d843'
down_revision: Union[str, None] = 'e20d2619bc78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('woocommerce_clients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('wc_url', sa.String(), nullable=False),
    sa.Column('consumer_key', sa.String(), nullable=False),
    sa.Column('consumer_secret', sa.String(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('woocommerce_reviews',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('store_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('product_name', sa.String(), nullable=False),
    sa.Column('reviewer', sa.String(), nullable=False),
    sa.Column('reviewer_email', sa.String(), nullable=False),
    sa.Column('review', sa.String(), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('date_created', sa.TIMESTAMP(timezone=False), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['store_id'], ['woocommerce_clients.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('woocommerce_reviews')
    op.drop_table('woocommerce_clients')

    pass
    # ### end Alembic commands ###
