"""empty message

Revision ID: 84a17e51af56
Revises: 7ac122129a98
Create Date: 2024-12-28 18:05:20.763716

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84a17e51af56'
down_revision: Union[str, None] = '7ac122129a98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'id', existing_type=sa.Integer(), type_=sa.BigInteger())
    op.alter_column('messages', 'id', existing_type=sa.Integer(), type_=sa.BigInteger())


def downgrade() -> None:
    pass
