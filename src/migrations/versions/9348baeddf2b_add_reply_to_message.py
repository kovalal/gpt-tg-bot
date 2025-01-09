"""Add reply_to_message

Revision ID: 9348baeddf2b
Revises: 1803f4234c60
Create Date: 2024-12-28 18:33:39.846953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9348baeddf2b'
down_revision: Union[str, None] = '1803f4234c60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('messages', sa.Column('reply_to_message', sa.BigInteger(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('messages', 'reply_to_message')
    # ### end Alembic commands ###
