"""change the wc credentials to nullable

Revision ID: 4f78b67863d1
Revises: 366cad3f6ab4
Create Date: 2023-11-18 13:23:32.639894

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4f78b67863d1'
down_revision: Union[str, None] = '366cad3f6ab4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #alter the columns of table e_commerce_integrations
    op.alter_column('e_commerce_integrations', 'wc_consumer_key',nullable=True)
    op.alter_column('e_commerce_integrations', 'wc_consumer_secret',nullable=True)
    pass


def downgrade() -> None:
    #alter the columns of table e_commerce_integrations
    op.alter_column('e_commerce_integrations', 'wc_consumer_key',nullable=False)
    op.alter_column('e_commerce_integrations', 'wc_consumer_secret',nullable=False)
    pass
